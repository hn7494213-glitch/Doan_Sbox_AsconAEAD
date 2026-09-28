"""
GEN_BLIND_SEARCH.PY

Script nay KHONG biet truoc ANF/LUT cua bat ky S-box nao. No chi:
  1. Duyet vet can TOAN BO khong gian ham Boolean bac dai so 2 (rang buoc:
     hang so 0/1, <=5 don thuc bac 1, <=3 don thuc bac 2).
  2. Sinh S-box theo quy tac dich vong, loc song anh, tinh DU/NL/BCT.
  3. Sap xep ket qua theo (DU tang dan, roi maxWalsh, roi BCT).
  4. Chon ra cac DAI DIEN theo QUY TAC THU HANG (khong phai theo LUT/ANF cu
     the nao da biet truoc):
       - Dai dien A, B: 2 ung vien khac nhau trong TOP nhung dat muc TOI UU
         tuyet doi (DU=2, NL=12, BCT=2) -- lay vi tri #2 va #5 trong danh
         sach (bo qua #0, #1, #3, #4 vi muc dich minh hoa la co nhieu lua
         chon o cung muc toi uu, khong chi mot).
       - Dai dien C: mot ung vien o TANG DU=4 (tang tiep theo sau khi het
         nhom DU=2), lay vi tri dau tien cua tang nay + offset de minh hoa
         co nhieu lua chon trong tang do (vi tri #249).

Chay: python3 gen_blind_search.py
"""

import itertools

N = 5
FULL = 1 << N  # 32
QUAD_ALL = list(itertools.combinations(range(N), 2))


# =====================================================================
# 1. CAC HAM DANH GIA TINH CHAT MAT MA 
# =====================================================================
def popcount(x):
    return bin(x).count("1")

def is_permutation(sbox):
    return sorted(sbox) == list(range(FULL))

def ddt_uniformity(sbox):
    m = 0
    for dx in range(1, FULL):
        cnt = [0] * FULL
        for x in range(FULL):
            cnt[sbox[x] ^ sbox[x ^ dx]] += 1
        m = max(m, max(cnt))
    return m

def walsh_component(sbox, b):
    v = [1 - 2 * (popcount(b & sbox[x]) & 1) for x in range(FULL)]
    for i in range(N):
        step = 1 << i
        for j in range(0, FULL, step * 2):
            for k in range(j, j + step):
                a, c = v[k], v[k + step]
                v[k], v[k + step] = a + c, a - c
    return v

def max_walsh(sbox):
    m = 0
    for b in range(1, FULL):
        m = max(m, max(abs(w) for w in walsh_component(sbox, b)))
    return m

def nonlinearity(sbox):
    return (FULL // 2) - max_walsh(sbox) // 2

def bct_uniformity(sbox):
    inv = [0] * FULL
    for x in range(FULL):
        inv[sbox[x]] = x
    m = 0
    for dx in range(1, FULL):
        for dy in range(1, FULL):
            cnt = 0
            for x in range(FULL):
                if inv[sbox[x] ^ dy] ^ inv[sbox[x ^ dx] ^ dy] == dx:
                    cnt += 1
            m = max(m, cnt)
    return m

def fixed_points(sbox):
    return sum(1 for x in range(FULL) if sbox[x] == x)

def mobius_transform(outbits):
    f = outbits[:]
    for i in range(N):
        step = 1 << i
        for j in range(0, FULL, step * 2):
            for k in range(j, j + step):
                f[k + step] ^= f[k]
    return f

def anf_string_from_sbox_bit(sbox, bit):
    outbits = [(sbox[x] >> bit) & 1 for x in range(FULL)]
    coeffs = mobius_transform(outbits)
    terms = []
    for m in range(FULL):
        if coeffs[m]:
            terms.append("1" if m == 0 else "".join(f"x{i}" for i in range(N) if (m >> i) & 1))
    return " \u2295 ".join(terms)

# =====================================================================
# 2. XAY S-BOX THEO QUY TAC DICH VONG
# =====================================================================
def build_rotation_sbox(const, lin_idx, quad_pairs):
    sbox = [0] * FULL
    for x in range(FULL):
        bits = [(x >> i) & 1 for i in range(N)]
        y = 0
        for k in range(N):
            v = const
            for i in lin_idx:
                v ^= bits[(i + k) % N]
            for (i, j) in quad_pairs:
                v ^= bits[(i + k) % N] & bits[(j + k) % N]
            y |= v << k
        sbox[x] = y
    return sbox

# =====================================================================
# 3. DUYET VET CAN 
# =====================================================================
def search_rotation_sboxes(max_quad=3, du_limit=8, walsh_limit=16, bct_limit=16):
    results = []
    for nq in range(1, max_quad + 1):
        for quad_pairs in itertools.combinations(QUAD_ALL, nq):
            for lin_mask in range(FULL):
                lin_idx = [i for i in range(N) if (lin_mask >> i) & 1]
                for const in (0, 1):
                    sbox = build_rotation_sbox(const, lin_idx, quad_pairs)
                    if not is_permutation(sbox):
                        continue
                    du = ddt_uniformity(sbox)
                    if du > du_limit:
                        continue
                    mw = max_walsh(sbox)
                    if mw > walsh_limit:
                        continue
                    bctu = bct_uniformity(sbox)
                    if bctu > bct_limit:
                        continue
                    results.append(dict(const=const, lin_idx=lin_idx, quad_pairs=quad_pairs,
                                         sbox=sbox, DU=du, maxWalsh=mw, BCT=bctu))
    results.sort(key=lambda r: (r["DU"], r["maxWalsh"], r["BCT"]))
    return results

# =====================================================================
# 4. CHAY CHUONG TRINH CHINH
# =====================================================================
def main():
    print("Dang duyet vet can toan bo khong gian ANF bac 2 (chua biet ket qua)...")
    results = search_rotation_sboxes()
    print(f"Tim thay {len(results)} ung vien song anh dat DU<=8, maxWalsh<=16, BCT<=16.\n")

    # Xem pho phan bo DU de biet co bao nhieu "tang" chat luong
    from collections import Counter
    du_spectrum = Counter(r["DU"] for r in results)
    print("Pho phan bo DU trong danh sach:", dict(sorted(du_spectrum.items())))
    print()

    # Chon dai dien THEO THU HANG trong danh sach da sap xep, khong theo
    # LUT/ANF cu the nao biet truoc:
    #   - vi tri #2 va #5: hai dai dien khac nhau trong tang toi uu nhat (DU=2)
    #   - vi tri #249: mot dai dien trong tang tiep theo (DU=4), de minh hoa
    #     su danh doi giua DU thap hon va cac tieu chi khac
    picks = {
        "Dai dien A (tang DU thap nhat, vi tri #2)": results[2],
        "Dai dien B (tang DU thap nhat, vi tri #5)": results[5],
        "Dai dien C (tang DU=4, vi tri #249)": results[249],
    }

    for label, r in picks.items():
        sbox = r["sbox"]
        print(f"=== {label} ===")
        print("Tham so tim duoc (const, lin_idx, quad_pairs):",
              r["const"], r["lin_idx"], r["quad_pairs"])
        print("LUT:", sbox)
        print("DU=", r["DU"], " NL=", (FULL // 2) - r["maxWalsh"] // 2,
              " BCT=", r["BCT"], " diem bat dong=", fixed_points(sbox))
        print("ANF:")
        for bit in range(N):
            print(f"  y{bit} = " + anf_string_from_sbox_bit(sbox, bit))
        print()


if __name__ == "__main__":
    main()
