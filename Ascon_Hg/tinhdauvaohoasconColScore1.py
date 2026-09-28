"""
ascon_sbox_metrics.py
=====================

Tính các bảng metric của S-box 5-bit dùng trong phân tích ASCON.

Chỉ cần thay SBOX là toàn bộ bảng tự tính lại.

Bao gồm:
  wr(b)       – differential restriction weight
  wc(b)       – linear restriction weight
  wrev_dts(a) – reverse differential weight
  wrev_lts(a) – reverse linear weight
"""

# ═══════════════════════════════════════════════════════════════
# SBOX (chỉ cần sửa phần này)
# ═══════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def popcount(x):
    return bin(x).count("1")

def dot(a,b):
    return popcount(a & b) & 1


# ═══════════════════════════════════════════════════════════════
# wr(b) — Differential restriction weight
#
# wr(b) = log2(|{S(x) ⊕ S(x⊕b)}|)
# ═══════════════════════════════════════════════════════════════

def compute_wr():

    wr=[0]*32

    for b in range(1,32):

        outputs=set()

        for x in range(32):
            outputs.add(SBOX[x]^SBOX[x^b])

        wr[b]=(len(outputs)).bit_length()-1

    return wr


# ═══════════════════════════════════════════════════════════════
# wc(b) — Linear restriction weight
#
# wc(b) = log2(|{a : LAT(a,b) ≠ 0}|)
# ═══════════════════════════════════════════════════════════════

def compute_wc():

    wc=[0]*32

    for b in range(1,32):

        compat=set()

        for a in range(32):

            cnt=0

            for x in range(32):

                if dot(a,x)==dot(b,SBOX[x]):
                    cnt+=1

            if cnt!=16:
                compat.add(a)

        wc[b]=(len(compat)).bit_length()-1

    return wc


# ═══════════════════════════════════════════════════════════════
# Reverse differential weight
#
# wrev_dts(a) = min wr(b)
#               s.t. ∃x: S(x)⊕S(x⊕b)=a
# ═══════════════════════════════════════════════════════════════

def compute_wrev_dts(wr):

    wrev=[0]*32

    for a in range(1,32):

        best=999

        for b in range(1,32):

            for x in range(32):

                if (SBOX[x]^SBOX[x^b])==a:
                    best=min(best,wr[b])
                    break

        wrev[a]=best

    return wrev


# ═══════════════════════════════════════════════════════════════
# Reverse linear weight
#
# wrev_lts(a) = min wc(b)
#               s.t. LAT(a,b) ≠ 0
# ═══════════════════════════════════════════════════════════════

def compute_wrev_lts(wc):

    wrev=[0]*32

    for a in range(1,32):

        best=999

        for b in range(1,32):

            cnt=0

            for x in range(32):

                if dot(a,x)==dot(b,SBOX[x]):
                    cnt+=1

            if cnt!=16:
                best=min(best,wc[b])

        wrev[a]=best

    return wrev


# ═══════════════════════════════════════════════════════════════
# Compute metrics
# ═══════════════════════════════════════════════════════════════

wr = compute_wr()
wc = compute_wc()

wrev_dts = compute_wrev_dts(wr)
wrev_lts = compute_wrev_lts(wc)


# ═══════════════════════════════════════════════════════════════
# Print results
# ═══════════════════════════════════════════════════════════════

def print_tables():

    print("wr (DTS weightListPerInput)")
    print(wr)
    print()

    print("wc (LTS weightListPerInput)")
    print(wc)
    print()

    print("wrev_dts (minRevWeightPerOutput)")
    print(wrev_dts)
    print()

    print("wrev_lts (minRevWeightPerOutput)")
    print(wrev_lts)
    print()


def main():
    print_tables()


if __name__ == "__main__":
    main()
