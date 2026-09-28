debug = False
debugpermutation = False

# === Ascon AEAD encryption and decryption ===

def ascon_encrypt(key, nonce, associateddata, plaintext, variant="Ascon-AEAD128", sbox_variant="ascon"):
    versions = {"Ascon-AEAD128": 1, "Ascon-AEAD128a": 2}
    assert variant in versions.keys()
    assert sbox_variant in ["ascon", "ascon2", "ascon3", "ascon4"]
    assert len(key) == 16 and len(nonce) == 16
    S = [0, 0, 0, 0, 0]
    k = len(key) * 8
    a = 12
    b = 6
    rate = 8

    if variant == "Ascon-AEAD128a":
        b = 8
        rate = 16

    ascon_initialize(S, k, rate, a, b, versions[variant], key, nonce, sbox_variant)
    ascon_process_associated_data(S, b, rate, associateddata, sbox_variant)
    ciphertext = ascon_process_plaintext(S, b, rate, plaintext, sbox_variant)
    tag = ascon_finalize(S, rate, a, key, sbox_variant)
    return ciphertext + tag


def ascon_decrypt(key, nonce, associateddata, ciphertext, variant="Ascon-AEAD128", sbox_variant="ascon"):
    versions = {"Ascon-AEAD128": 1, "Ascon-AEAD128a": 2}
    assert variant in versions.keys()
    assert sbox_variant in ["ascon", "ascon2", "ascon3", "ascon4"]
    assert len(key) == 16 and len(nonce) == 16 and len(ciphertext) >= 16
    S = [0, 0, 0, 0, 0]
    k = len(key) * 8
    a = 12
    b = 6
    rate = 8

    if variant == "Ascon-AEAD128a":
        b = 8
        rate = 16

    ascon_initialize(S, k, rate, a, b, versions[variant], key, nonce, sbox_variant)
    ascon_process_associated_data(S, b, rate, associateddata, sbox_variant)
    plaintext = ascon_process_ciphertext(S, b, rate, ciphertext[:-16], sbox_variant)
    tag = ascon_finalize(S, rate, a, key, sbox_variant)
    if tag == ciphertext[-16:]:
        return plaintext
    else:
        return None


# === Ascon AEAD building blocks ===

def ascon_initialize(S, k, rate, a, b, version, key, nonce, sbox_variant="ascon"):
    iv = to_bytes([k, rate * 8, a, b]) + int_to_bytes(0, (160 - k) // 8)

    S[0], S[1], S[2], S[3], S[4] = bytes_to_state(iv + key + nonce)
    if debug:
        printstate(S, "initial value:")
    ascon_permutation(S, a, sbox_variant)
    zero_key = bytes_to_state(zero_bytes(40 - len(key)) + key)
    S[0] ^= zero_key[0]
    S[1] ^= zero_key[1]
    S[2] ^= zero_key[2]
    S[3] ^= zero_key[3]
    S[4] ^= zero_key[4]
    if debug:
        printstate(S, "initialization:")


def ascon_process_associated_data(S, b, rate, associateddata, sbox_variant="ascon"):
    if len(associateddata) > 0:
        a_padding = to_bytes([0x01]) + zero_bytes(rate - (len(associateddata) % rate) - 1)
        a_padded = associateddata + a_padding

        for block in range(0, len(a_padded), rate):
            S[0] ^= bytes_to_int(a_padded[block:block + 8])
            if rate == 16:
                S[1] ^= bytes_to_int(a_padded[block + 8:block + 16])

            ascon_permutation(S, b, sbox_variant)

    S[4] ^= 1
    if debug:
        printstate(S, "process associated data:")


def ascon_process_plaintext(S, b, rate, plaintext, sbox_variant="ascon"):
    p_lastlen = len(plaintext) % rate
    p_padding = to_bytes([0x01]) + zero_bytes(rate - p_lastlen - 1)
    p_padded = plaintext + p_padding

    ciphertext = to_bytes([])
    for block in range(0, len(p_padded) - rate, rate):
        S[0] ^= bytes_to_int(p_padded[block:block + 8])
        ciphertext += int_to_bytes(S[0], 8)

        if rate == 16:
            S[1] ^= bytes_to_int(p_padded[block + 8:block + 16])
            ciphertext += int_to_bytes(S[1], 8)

        ascon_permutation(S, b, sbox_variant)

    block = len(p_padded) - rate
    S[0] ^= bytes_to_int(p_padded[block:block + 8])
    S[1] ^= bytes_to_int(p_padded[block + 8:block + 16])

    ciphertext += (
        int_to_bytes(S[0], 8)[:min(8, p_lastlen)] +
        int_to_bytes(S[1], 8)[:max(0, p_lastlen - 8)]
    )
    if debug:
        printstate(S, "process plaintext:")
    return ciphertext


def ascon_process_ciphertext(S, b, rate, ciphertext, sbox_variant="ascon"):
    c_lastlen = len(ciphertext) % rate
    c_padded = ciphertext + zero_bytes(rate - c_lastlen)

    plaintext = to_bytes([])
    for block in range(0, len(c_padded) - rate, rate):
        if rate == 8:
            Ci = bytes_to_int(c_padded[block:block + 8])
            plaintext += int_to_bytes(S[0] ^ Ci, 8)
            S[0] = Ci
        elif rate == 16:
            Ci = (
                bytes_to_int(c_padded[block:block + 8]),
                bytes_to_int(c_padded[block + 8:block + 16])
            )
            plaintext += int_to_bytes(S[0] ^ Ci[0], 8) + int_to_bytes(S[1] ^ Ci[1], 8)
            S[0] = Ci[0]
            S[1] = Ci[1]
        ascon_permutation(S, b, sbox_variant)

    block = len(c_padded) - rate
    c_padx = zero_bytes(c_lastlen) + to_bytes([0x01]) + zero_bytes(rate - c_lastlen - 1)
    c_mask = zero_bytes(c_lastlen) + ff_bytes(rate - c_lastlen)

    if rate == 8:
        Ci = bytes_to_int(c_padded[block:block + 8])
        plaintext += int_to_bytes(S[0] ^ Ci, 8)[:c_lastlen]
        S[0] = (S[0] & bytes_to_int(c_mask[0:8])) ^ Ci ^ bytes_to_int(c_padx[0:8])

    elif rate == 16:
        Ci = (
            bytes_to_int(c_padded[block:block + 8]),
            bytes_to_int(c_padded[block + 8:block + 16])
        )
        plaintext += (int_to_bytes(S[0] ^ Ci[0], 8) + int_to_bytes(S[1] ^ Ci[1], 8))[:c_lastlen]
        S[0] = (S[0] & bytes_to_int(c_mask[0:8])) ^ Ci[0] ^ bytes_to_int(c_padx[0:8])
        S[1] = (S[1] & bytes_to_int(c_mask[8:16])) ^ Ci[1] ^ bytes_to_int(c_padx[8:16])

    if debug:
        printstate(S, "process ciphertext:")
    return plaintext


def ascon_finalize(S, rate, a, key, sbox_variant="ascon"):
    assert len(key) == 16
    S[rate // 8 + 0] ^= bytes_to_int(key[0:8])
    S[rate // 8 + 1] ^= bytes_to_int(key[8:16])
    ascon_permutation(S, a, sbox_variant)

    S[3] ^= bytes_to_int(key[0:8])
    S[4] ^= bytes_to_int(key[8:16])
    tag = int_to_bytes(S[3], 8) + int_to_bytes(S[4], 8)
    if debug:
        printstate(S, "finalization:")
    return tag


# === S-box layers ===

def substitution_ascon_original(S):
    S[0] ^= S[4]
    S[4] ^= S[3]
    S[2] ^= S[1]
    T = [(S[i] ^ 0xFFFFFFFFFFFFFFFF) & S[(i + 1) % 5] for i in range(5)]
    for i in range(5):
        S[i] ^= T[(i + 1) % 5]
    S[1] ^= S[0]
    S[0] ^= S[4]
    S[3] ^= S[2]
    S[2] ^= 0xFFFFFFFFFFFFFFFF


def substitution_ascon2(S):
    x0, x1, x2, x3, x4 = S

    S[0] = x1 ^ (x0 & x1) ^ x2 ^ (x0 & x2) ^ x3 ^ x4 ^ (x2 & x4)
    S[1] = x0 ^ x2 ^ (x1 & x2) ^ x3 ^ (x0 & x3) ^ (x1 & x3) ^ x4
    S[2] = x0 ^ x1 ^ x3 ^ (x2 & x3) ^ x4 ^ (x1 & x4) ^ (x2 & x4)
    S[3] = x0 ^ x1 ^ x2 ^ (x0 & x2) ^ (x0 & x3) ^ x4 ^ (x3 & x4)
    S[4] = x0 ^ x1 ^ x2 ^ x3 ^ (x1 & x3) ^ (x0 & x4) ^ (x1 & x4)


def substitution_ascon3(S):
    MASK64 = 0xFFFFFFFFFFFFFFFF
    x0, x1, x2, x3, x4 = S

    S[0] = MASK64 ^ x1 ^ x3 ^ (x0 & x1) ^ (x0 & x2) ^ (x3 & x4)
    S[1] = MASK64 ^ x2 ^ x4 ^ (x1 & x2) ^ (x1 & x3) ^ (x0 & x4)
    S[2] = MASK64 ^ x0 ^ x3 ^ (x2 & x3) ^ (x2 & x4) ^ (x0 & x1)
    S[3] = MASK64 ^ x1 ^ x4 ^ (x3 & x4) ^ (x0 & x3) ^ (x1 & x2)
    S[4] = MASK64 ^ x0 ^ x2 ^ (x0 & x4) ^ (x1 & x4) ^ (x2 & x3)


def substitution_ascon4(S):
    MASK64 = 0xFFFFFFFFFFFFFFFF
    x0, x1, x2, x3, x4 = S

    S[0] = MASK64 ^ x0 ^ x1 ^ x2 ^ x4 ^ (x0 & x1) ^ (x0 & x2) ^ (x1 & x3)
    S[1] = MASK64 ^ x0 ^ x1 ^ x2 ^ x3 ^ (x1 & x2) ^ (x1 & x3) ^ (x2 & x4)
    S[2] = MASK64 ^ x1 ^ x2 ^ x3 ^ x4 ^ (x0 & x3) ^ (x2 & x3) ^ (x2 & x4)
    S[3] = MASK64 ^ x0 ^ x2 ^ x3 ^ x4 ^ (x0 & x3) ^ (x1 & x4) ^ (x3 & x4)
    S[4] = MASK64 ^ x0 ^ x1 ^ x3 ^ x4 ^ (x0 & x2) ^ (x0 & x4) ^ (x1 & x4)


def apply_substitution_layer(S, sbox_variant="ascon"):
    if sbox_variant == "ascon":
        substitution_ascon_original(S)
    elif sbox_variant == "ascon2":
        substitution_ascon2(S)
    elif sbox_variant == "ascon3":
        substitution_ascon3(S)
    elif sbox_variant == "ascon4":
        substitution_ascon4(S)
    else:
        raise ValueError(f"Unsupported sbox_variant: {sbox_variant}")


# === Ascon permutation ===

def ascon_permutation(S, rounds=1, sbox_variant="ascon"):
    assert rounds <= 12
    if debugpermutation:
        printwords(S, f"permutation input ({sbox_variant}):")
    num = 0
    for r in range(12 - rounds, 12):
        S[2] ^= (0xf0 - r * 0x10 + r * 0x1)
        if debugpermutation:
            print("Round", num)
            num += 1
            printwords(S, "round constant addition:")

        apply_substitution_layer(S, sbox_variant)
        if debugpermutation:
            printwords(S, f"substitution layer ({sbox_variant}):")

        S[0] ^= rotr(S[0], 19) ^ rotr(S[0], 28)
        S[1] ^= rotr(S[1], 61) ^ rotr(S[1], 39)
        S[2] ^= rotr(S[2], 1) ^ rotr(S[2], 6)
        S[3] ^= rotr(S[3], 10) ^ rotr(S[3], 17)
        S[4] ^= rotr(S[4], 7) ^ rotr(S[4], 41)
        if debugpermutation:
            printwords(S, "linear diffusion layer:")


# === helper functions ===

def get_random_bytes(num):
    import os
    return to_bytes(os.urandom(num))


def zero_bytes(n):
    return n * b"\x00"


def ff_bytes(n):
    return n * b"\xFF"


def to_bytes(l):
    return bytes(bytearray(l))


def bytes_to_int(b):
    return sum([bi << (8 * (len(b) - 1 - i)) for i, bi in enumerate(b)])


def int_to_bytes(integer, nbytes):
    return to_bytes([
        (integer >> (8 * (nbytes - 1 - i))) % 256
        for i in range(nbytes)
    ])


def bytes_to_state(data_bytes):
    return [bytes_to_int(data_bytes[8 * w:8 * (w + 1)]) for w in range(5)]


def rotr(val, r):
    return (val >> r) | ((val & (1 << r) - 1) << (64 - r))


def bytes_to_hex(b):
    return b.hex()


def printstate(S, description=""):
    print(" " + description)
    print(" ".join(["{s:016x}".format(s=s) for s in S]))


def printwords(S, description=""):
    print(" " + description)
    print("\n".join(["  x{i}={s:016x}".format(**locals()) for i, s in enumerate(S)]))


# === test helpers ===

def functional_test_case(name, key, nonce, ad, pt, variant, sbox_variant):
    ct_tag = ascon_encrypt(key, nonce, ad, pt, variant=variant, sbox_variant=sbox_variant)
    recovered = ascon_decrypt(key, nonce, ad, ct_tag, variant=variant, sbox_variant=sbox_variant)
    ok_recover = (recovered == pt)

    tampered_ct = bytearray(ct_tag)
    if len(ct_tag) > 16:
        tampered_ct[0] ^= 0x01
    else:
        tampered_ct[-1] ^= 0x01
    tampered_recovered = ascon_decrypt(key, nonce, ad, bytes(tampered_ct), variant=variant, sbox_variant=sbox_variant)
    ok_tamper_ct = (tampered_recovered is None)

    tampered_tag = bytearray(ct_tag)
    tampered_tag[-1] ^= 0x01
    tampered_tag_recovered = ascon_decrypt(key, nonce, ad, bytes(tampered_tag), variant=variant, sbox_variant=sbox_variant)
    ok_tamper_tag = (tampered_tag_recovered is None)

    return {
        "name": name,
        "plaintext_len": len(pt),
        "ad_len": len(ad),
        "recover_ok": ok_recover,
        "tag_accept_ok": ok_recover,
        "tamper_ciphertext_detected": ok_tamper_ct,
        "tamper_tag_detected": ok_tamper_tag,
    }


def run_functional_tests(sbox_variant="ascon", variant="Ascon-AEAD128"):
    key = b'hL;\xbe}Y \x1c\x94\x17d\x9e\x8d\x88\xf5\xa3'
    nonce = b'OV\xbc ,\xf3\xde\xf0hy\xd2\xf3\xd1\x99.\xa0'

    cases = [
        ("Bản rõ ngắn, AD rỗng", key, nonce, b"", b"ASCON", variant, sbox_variant),
        ("Bản rõ ngắn, AD khác rỗng", key, nonce, b"associate-data", b"ASCON", variant, sbox_variant),
        ("Bản rõ dài, AD rỗng", key, nonce, b"", b"A" * 1024, variant, sbox_variant),
        ("Bản rõ dài, AD khác rỗng", key, nonce, b"metadata-associated-data", b"B" * 1024, variant, sbox_variant),
    ]

    results = [functional_test_case(*case) for case in cases]

    sbox_name_map = {
        "ascon": "Ascon gốc",
        "ascon2": "Ascon2",
        "ascon3": "Ascon3",
        "ascon4": "Ascon4",
    }
    sbox_display = sbox_name_map.get(sbox_variant, sbox_variant)

    print(f"\n=== Kiểm thử chức năng cho {variant} với {sbox_display} ===")
    print(
        f"{'Trường hợp':<30} {'PT(B)':>6} {'AD(B)':>6} "
        f"{'Khôi phục':>10} {'Tag đúng':>10} {'Lật bit CT':>11} "
        f"{'Lật bit tag':>12} {'Tổng thể':>9}"
    )
    print("-" * 110)

    for r in results:
        recover_status = "ĐẠT" if r["recover_ok"] else "KHÔNG ĐẠT"
        tag_status = "ĐẠT" if r["tag_accept_ok"] else "KHÔNG ĐẠT"
        ct_status = "ĐẠT" if r["tamper_ciphertext_detected"] else "KHÔNG ĐẠT"
        tag_flip_status = "ĐẠT" if r["tamper_tag_detected"] else "KHÔNG ĐẠT"
        overall_status = (
            "ĐẠT"
            if r["recover_ok"] and r["tag_accept_ok"] and r["tamper_ciphertext_detected"] and r["tamper_tag_detected"]
            else "KHÔNG ĐẠT"
        )

        print(
            f"{r['name']:<30} {r['plaintext_len']:>6} {r['ad_len']:>6} "
            f"{recover_status:>10} {tag_status:>10} {ct_status:>11} "
            f"{tag_flip_status:>12} {overall_status:>9}"
        )

    print("\nVị trí gây sai hỏng được sử dụng:")
    print("- Lật 1 bit bản mã: ciphertext[0] ^= 0x01")
    print("- Lật 1 bit thẻ xác thực: tag[-1] ^= 0x01")

    all_ok = all(
        r["recover_ok"] and r["tag_accept_ok"] and r["tamper_ciphertext_detected"] and r["tamper_tag_detected"]
        for r in results
    )
    print(f"\nKết quả tổng thể: {'ĐẠT' if all_ok else 'KHÔNG ĐẠT'}")
    return results


# === some demo if called directly ===

def demo_print(data):
    maxlen = max([len(text) for (text, val) in data])
    for text, val in data:
        print("{text}:{align} 0x{val} ({length} bytes)".format(
            text=text,
            align=((maxlen - len(text)) * " "),
            val=bytes_to_hex(val),
            length=len(val)
        ))


def demo_aead(variant="Ascon-AEAD128a", sbox_variant="ascon"):
    assert variant in ["Ascon-AEAD128", "Ascon-AEAD128a"]
    print("=== Demo mã hóa và giải mã dùng {variant} với {sbox_variant} ===".format(
        variant=variant, sbox_variant=sbox_variant
    ))
    
    key   = get_random_bytes(16)  # zero_bytes(16)
    #key = b'hL;\xbe}Y \x1c\x94\x17d\x9e\x8d\x88\xf5\xa3'
    nonce = get_random_bytes(16)  # zero_bytes(16)
    #nonce = b'OV\xbc ,\xf3\xde\xf0hy\xd2\xf3\xd1\x99.\xa0'
    associateddata = b"associate-data"
    plaintext = b"ASCON"

    ciphertext = ascon_encrypt(key, nonce, associateddata, plaintext, variant, sbox_variant)
    receivedplaintext = ascon_decrypt(key, nonce, associateddata, ciphertext, variant, sbox_variant)
    if receivedplaintext is None:
        print("Xác thực thất bại!")

    demo_print([
        ("key", key),
        ("nonce", nonce),
        ("plaintext", plaintext),
        ("ass.data", associateddata),
        ("ciphertext", ciphertext[:-16]),
        ("tag", ciphertext[-16:]),
        ("received", receivedplaintext if receivedplaintext is not None else b""),
    ])


if __name__ == "__main__":
    demo_aead("Ascon-AEAD128", "ascon")
    demo_aead("Ascon-AEAD128", "ascon2")
    demo_aead("Ascon-AEAD128", "ascon3")
    demo_aead("Ascon-AEAD128", "ascon4")
    

    run_functional_tests("ascon", "Ascon-AEAD128")
    run_functional_tests("ascon2", "Ascon-AEAD128")
    run_functional_tests("ascon3", "Ascon-AEAD128")
    run_functional_tests("ascon4", "Ascon-AEAD128")
def main():
    demo_aead("Ascon-AEAD128", "ascon")
    demo_aead("Ascon-AEAD128", "ascon2")
    demo_aead("Ascon-AEAD128", "ascon3")
    demo_aead("Ascon-AEAD128", "ascon4")

    run_functional_tests("ascon", "Ascon-AEAD128")
    run_functional_tests("ascon2", "Ascon-AEAD128")
    run_functional_tests("ascon3", "Ascon-AEAD128")
    run_functional_tests("ascon4", "Ascon-AEAD128")
    
if __name__ == "__main__":
    main()