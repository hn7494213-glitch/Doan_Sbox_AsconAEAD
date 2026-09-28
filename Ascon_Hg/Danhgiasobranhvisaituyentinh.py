 
# =====================================================================
# 1. CHON S-HOP CAN DANH GIA (chi giu 1 khoi khong bi comment)
# =====================================================================
 
# Ascon (goc):
# SBOX = [
#     0x04,0x0b,0x1f,0x14,0x1a,0x15,0x09,0x02,
#     0x1b,0x05,0x08,0x12,0x1d,0x03,0x06,0x1c,
#     0x1e,0x13,0x07,0x0e,0x00,0x0d,0x11,0x18,
#     0x10,0x0c,0x01,0x19,0x16,0x0a,0x0f,0x17,
# ]
 
# Ascon2:
# SBOX = [
#     0x13,0x1b,0x07,0x1d,0x1f,0x14,0x03,0x1a,
#     0x11,0x01,0x00,0x02,0x0f,0x1c,0x16,0x17,
#     0x0a,0x06,0x0e,0x10,0x04,0x0b,0x08,0x15,
#     0x19,0x0d,0x18,0x1e,0x05,0x12,0x0c,0x09,
# ]
#SBOX = [
#   0x00,0x1e,0x1d,0x02,0x1b,0x0c,0x04,0x12,
#   0x17,0x03,0x18,0x0d,0x08,0x15,0x05,0x19,
#   0x0f,0x01,0x06,0x09,0x11,0x16,0x1a,0x1c,
#   0x10,0x14,0x0b,0x0e,0x0a,0x07,0x13,0x1f,
# ]

# Ascon3:
# SBOX = [
 #    0x1f,0x0b,0x16,0x07,0x0d,0x18,0x0e,0x1e,
 #    0x1a,0x06,0x11,0x08,0x1c,0x01,0x1d,0x05,
  #   0x15,0x13,0x0c,0x0f,0x03,0x04,0x10,0x12,
 #    0x19,0x17,0x02,0x09,0x1b,0x14,0x0a,0x00,
 # ]
 
# Ascon4:
#SBOX = [
#     0x00,0x01,0x08,0x0f,0x12,0x07,0x03,0x10,
#    0x1d,0x06,0x11,0x0c,0x18,0x17,0x0d,0x04,
#    0x1e,0x15,0x19,0x14,0x05,0x1a,0x1b,0x02,
#    0x1f,0x0e,0x1c,0x0b,0x13,0x16,0x09,0x0a,
#]
SBOX = [
     0x1f,0x04,0x08,0x12,0x10,0x1a,0x05,0x0e,
     0x01,0x16,0x15,0x03,0x0a,0x0c,0x1c,0x1b,
     0x02,0x09,0x0d,0x07,0x0b,0x11,0x06,0x1d,
     0x14,0x13,0x18,0x1e,0x19,0x0f,0x17,0x00,
 ]

#Ascon5
#SBOX = [
#    0x00,0x1d,0x0f,0x13,0x1b,0x03,0x1c,0x05,
#    0x1e,0x11,0x18,0x16,0x07,0x0d,0x09,0x02,
#    0x17,0x0e,0x0c,0x14,0x06,0x1a,0x15,0x08,
#    0x19,0x12,0x0b,0x01,0x0a,0x04,0x10,0x1f,
#]

N = 5           # so bit cua S-hop
FULL = 1 << N   # 32
 
 
# =====================================================================
# 2. CAC HAM TIEN ICH
# =====================================================================
def popcount(x):
    return bin(x).count("1")
 
 
def is_permutation(sbox):
    return sorted(sbox) == list(range(FULL))
 
 
def build_ddt(sbox):
    """Bang phan bo vi sai DDT[dx][dy] = so cap x thoa S(x) xor S(x xor dx) = dy."""
    ddt = [[0] * FULL for _ in range(FULL)]
    for x in range(FULL):
        for dx in range(FULL):
            dy = sbox[x] ^ sbox[x ^ dx]
            ddt[dx][dy] += 1
    return ddt
 
 
def walsh_component(sbox, b):
    """Bien doi Walsh-Hadamard cua thanh phan tuyen tinh f_b(x) = <b, S(x)> (parity)."""
    v = [1 - 2 * (popcount(b & sbox[x]) & 1) for x in range(FULL)]
    for i in range(N):
        step = 1 << i
        for j in range(0, FULL, step * 2):
            for k in range(j, j + step):
                u, w = v[k], v[k + step]
                v[k], v[k + step] = u + w, u - w
    return v
 
 
def build_lat_nonzero_mask_pairs(sbox):
    """Tra ve tap hop cac cap (a,b) voi a,b != 0 ma tuong quan Walsh W(a,b) != 0."""
    pairs = set()
    for b in range(1, FULL):
        W = walsh_component(sbox, b)
        for a in range(1, FULL):
            if W[a] != 0:
                pairs.add((a, b))
    return pairs
 
 
# =====================================================================
# 3. SO NHANH VI SAI (DIFFERENTIAL BRANCH NUMBER)
# =====================================================================
def differential_branch_number(sbox):
    ddt = build_ddt(sbox)
    best = None
    for dx in range(1, FULL):          # dx = 0 khong tinh (khong phai vi sai thuc su)
        for dy in range(FULL):
            if ddt[dx][dy] != 0:
                b = popcount(dx) + popcount(dy)
                if best is None or b < best:
                    best = b
    return best
 
 
# =====================================================================
# 4. SO NHANH TUYEN TINH (LINEAR BRANCH NUMBER)
# =====================================================================
def linear_branch_number(sbox):
    pairs = build_lat_nonzero_mask_pairs(sbox)   # a,b deu != 0
    best = None
    for (a, b) in pairs:
        w = popcount(a) + popcount(b)
        if best is None or w < best:
            best = w
    return best
 
 
# =====================================================================
# (Tuy chon them) DU va NL de doi chieu nhanh, khong bat buoc dung
# =====================================================================
def diff_uniformity(sbox):
    ddt = build_ddt(sbox)
    m = 0
    for dx in range(1, FULL):
        for dy in range(FULL):
            if ddt[dx][dy] > m:
                m = ddt[dx][dy]
    return m
 
 
def nonlinearity(sbox):
    m = 0
    for b in range(1, FULL):
        W = walsh_component(sbox, b)
        m = max(m, max(abs(w) for w in W))
    return (FULL // 2) - m // 2
 
 
# =====================================================================
# 5. MAIN: bo comment dong nao muon tinh, comment lai dong khong can
# =====================================================================
def main():
    print("S-hop dang danh gia (LUT):", SBOX)
    print("La song anh hop le:", is_permutation(SBOX))
    print()
 
    # --- So nhanh vi sai ---
    print("So nhanh vi sai (differential branch number)  B_D =", differential_branch_number(SBOX))
 
    # --- So nhanh tuyen tinh ---
    print("So nhanh tuyen tinh (linear branch number)     B_L =", linear_branch_number(SBOX))
 
    # --- (tuy chon) DU / NL de doi chieu ---
    # print("Do dong deu vi sai (DU) =", diff_uniformity(SBOX))
    # print("Do phi tuyen (NL)       =", nonlinearity(SBOX))


if __name__ == "__main__":
    main()
