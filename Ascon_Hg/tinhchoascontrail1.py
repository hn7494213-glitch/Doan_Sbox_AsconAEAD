"""
compute_ascon_trail_tables.py
Tính các bảng cho AsconTrailTool với bất kỳ S-box 5-bit nào.
Chỉ cần thay SBOX bên dưới rồi chạy lại.
"""

import math

# ══════════════════════════════════════════
# THAY S-BOX TẠI ĐÂY
# ══════════════════════════════════════════
# Ascon:
#SBOX = [
#     0x04,0x0b,0x1f,0x14,0x1a,0x15,0x09,0x02,
#     0x1b,0x05,0x08,0x12,0x1d,0x03,0x06,0x1c,
#     0x1e,0x13,0x07,0x0e,0x00,0x0d,0x11,0x18,
#     0x10,0x0c,0x01,0x19,0x16,0x0a,0x0f,0x17,
#]

# Ascon2:
#SBOX = [
#     0x13,0x1b,0x07,0x1d,0x1f,0x14,0x03,0x1a,
#     0x11,0x01,0x00,0x02,0x0f,0x1c,0x16,0x17,
#     0x0a,0x06,0x0e,0x10,0x04,0x0b,0x08,0x15,
#     0x19,0x0d,0x18,0x1e,0x05,0x12,0x0c,0x09,
# ]

# SBOX = [
#    0x00,0x1e,0x1d,0x02,0x1b,0x0c,0x04,0x12,
#    0x17,0x03,0x18,0x0d,0x08,0x15,0x05,0x19,
#    0x0f,0x01,0x06,0x09,0x11,0x16,0x1a,0x1c,
#    0x10,0x14,0x0b,0x0e,0x0a,0x07,0x13,0x1f,
#  ]

# Ascon3:
#SBOX = [
#    0x1f,0x0b,0x16,0x07,0x0d,0x18,0x0e,0x1e,
#    0x1a,0x06,0x11,0x08,0x1c,0x01,0x1d,0x05,
#    0x15,0x13,0x0c,0x0f,0x03,0x04,0x10,0x12,
#    0x19,0x17,0x02,0x09,0x1b,0x14,0x0a,0x00,
#]

# Ascon4:
#SBOX = [
#     0x00,0x01,0x08,0x0f,0x12,0x07,0x03,0x10,
#     0x1d,0x06,0x11,0x0c,0x18,0x17,0x0d,0x04,
#     0x1e,0x15,0x19,0x14,0x05,0x1a,0x1b,0x02,
#     0x1f,0x0e,0x1c,0x0b,0x13,0x16,0x09,0x0a,
# ]
SBOX = [
     0x1f,0x04,0x08,0x12,0x10,0x1a,0x05,0x0e,
     0x01,0x16,0x15,0x03,0x0a,0x0c,0x1c,0x1b,
     0x02,0x09,0x0d,0x07,0x0b,0x11,0x06,0x1d,
     0x14,0x13,0x18,0x1e,0x19,0x0f,0x17,0x00,
 ]

# ══════════════════════════════════════════
# DDT và LAT
# ══════════════════════════════════════════
def build_DDT(s):
    d = [[0]*32 for _ in range(32)]
    for b in range(32):
        for x in range(32):
            d[b][s[x ^ b] ^ s[x]] += 1
    return d

def build_LAT(s):
    l = [[0]*32 for _ in range(32)]
    for a in range(32):
        for b in range(32):
            l[a][b] = sum(
                1 - 2 * ((bin(a & x).count('1') + bin(b & s[x]).count('1')) & 1)
                for x in range(32)
            )
    return l


# ══════════════════════════════════════════
# Weight
# ══════════════════════════════════════════
def diff_w(ddt, b):
    if b == 0: return 0
    return int(round(5 - math.log2(max(ddt[b]))))

def lin_w(lat, b):
    if b == 0: return 0
    mx = max(abs(lat[a][b]) for a in range(1, 32))
    return int(round(-2 * math.log2(mx / 32))) if mx else 0


# ══════════════════════════════════════════
# Không gian affine GF(2) — khớp với C++
#
# Quy tắc:
#   1. offset = phần tử có ít bit 1 nhất, tie-break giá trị nhỏ hơn
#   2. Gaussian elimination theo LSB (lowest set bit làm pivot)
#      với backward reduction (RREF)
#   3. Sắp xếp basis theo giá trị tăng dần
# ══════════════════════════════════════════
def affine_space(elems):
    if not elems:
        return 0, []

    # Chọn offset = min popcount, tie-break giá trị nhỏ
    off = min(elems, key=lambda x: (bin(x).count('1'), x))
    vecs = [e ^ off for e in sorted(elems) if e != off]

    basis = []
    pivot_bits = []
    for v in vecs:
        cur = v
        # forward reduce
        for i, b in enumerate(basis):
            if cur >> pivot_bits[i] & 1:
                cur ^= b
        if cur:
            pb = (cur & -cur).bit_length() - 1   # lowest set bit
            basis.append(cur)
            pivot_bits.append(pb)
            # backward reduce các basis trước
            for i in range(len(basis) - 1):
                if basis[i] >> pb & 1:
                    basis[i] ^= cur

    basis.sort()
    return off, basis


# ══════════════════════════════════════════
# Tính bảng
# ══════════════════════════════════════════
def make_tables(wl, nonzero_fn):
    direct  = [sorted(a for a in range(32) if nonzero_fn(a, b)) for b in range(32)]
    affine  = [affine_space(direct[b]) for b in range(32)]
    reverse = []
    for a in range(32):
        bs = [b for b in range(1, 32) if nonzero_fn(a, b)]
        bs.sort(key=lambda b: (wl[b], b))
        reverse.append(bs)
    wr = [[wl[b] for b in row] for row in reverse]
    mr = [min((wl[b] for b in row), default=0) for row in reverse]
    return direct, affine, reverse, wr, mr


# ══════════════════════════════════════════
# In C++
# ══════════════════════════════════════════
def print_cpp(wl, direct, affine, reverse, wr, mr, dts, label):
    idx = "  ".join(f"{i:2}" for i in range(32))
    print(f"\n{'='*68}")
    print(f"// DTS={dts}  ({label})")
    print(f"{'='*68}")

    print(f"// Input           =   {idx}")
    print("weightListPerInput = { " + ", ".join(map(str, wl)) + " };")

    print("\ndirectOutputListPerInput = { {0x00},")
    for b in range(1, 32):
        lst = ", ".join(f"0x{v:02X}" for v in direct[b])
        print(f"    {{{lst}}}{',' if b < 31 else ' };'}")

    print("\naffinePerInput = { AffineSpaceOfColumns(0,{}),")
    for b in range(1, 32):
        off, gens = affine[b]
        gs = ", ".join(f"0x{g:02X}" for g in gens)
        print(f"    AffineSpaceOfColumns(0x{off:02X}, {{{gs}}}){',' if b < 31 else ' };'}")

    print("\n// these are ordered by their weight")
    print("reverseOutputListPerInput = { {0x00},")
    for a in range(1, 32):
        lst = ", ".join(f"0x{v:02X}" for v in reverse[a])
        print(f"    {{{lst}}}{',' if a < 31 else ' };'}")

    print("\n// the weight of each compatible input pattern")
    print("weightReverseOutputListPerInput = { {0},      // 0")
    for a in range(1, 32):
        ws = ", ".join(map(str, wr[a]))
        print(f"    {{{ws}}}{',' if a < 31 else ' };'}  //{a:2}")

    print(f"\n//                            {idx}")
    print("minRevWeightListPerOutput = { " + ", ".join(map(str, mr)) + " };")


# ══════════════════════════════════════════
# Main
# ══════════════════════════════════════════
# ══════════════════════════════════════════
# Main
# ══════════════════════════════════════════
def main():
    assert len(SBOX) == 32 and sorted(SBOX) == list(range(32)), "S-box không hợp lệ"

    DDT = build_DDT(SBOX)
    LAT = build_LAT(SBOX)

    # DTS=1  Differential
    wl_d = [diff_w(DDT, b) for b in range(32)]
    d_dir, d_aff, d_rev, d_wr, d_mr = make_tables(
        wl_d,
        lambda a, b: DDT[b][a] > 0
    )

    print_cpp(
        wl_d,
        d_dir,
        d_aff,
        d_rev,
        d_wr,
        d_mr,
        dts=1,
        label="DIFFERENTIAL"
    )

    # DTS=0  Linear
    wl_l = [lin_w(LAT, b) for b in range(32)]
    l_dir, l_aff, l_rev, l_wr, l_mr = make_tables(
        wl_l,
        lambda a, b: LAT[a][b] != 0
    )

    print_cpp(
        wl_l,
        l_dir,
        l_aff,
        l_rev,
        l_wr,
        l_mr,
        dts=0,
        label="LINEAR"
    )


if __name__ == "__main__":
    main()