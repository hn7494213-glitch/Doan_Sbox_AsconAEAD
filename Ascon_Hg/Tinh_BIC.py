import numpy as np
from itertools import combinations

SBOX = [
    0x1f,0x04,0x08,0x12,0x10,0x1a,0x05,0x0e,
         0x01,0x16,0x15,0x03,0x0a,0x0c,0x1c,0x1b,
         0x02,0x09,0x0d,0x07,0x0b,0x11,0x06,0x1d,
         0x14,0x13,0x18,0x1e,0x19,0x0f,0x17,0x00,
]
N    = 5        # số bit (Ascon: 5x5)
SIZE = 1 << N   # số phần tử = 32

def bic(sbox):
    # Ma trận bit ra: out[j][x] = bit thứ j của S(x)
    out = np.array(
        [[(sbox[x] >> (N-1-j)) & 1 for x in range(SIZE)] for j in range(N)],
        dtype=np.int8
    )
    xs, corrs = np.arange(SIZE), []
    for i in range(N):
        # Bước 2-3: flip bit i, tính biến thác đổ Δi_fj(x)
        d = (out ^ out[:, xs ^ (1 << (N-1-i))]).astype(np.int8)
        # Bước 4: tính |correlation| mọi cặp (j,k)
        for j, k in combinations(range(N), 2):
            ex, ey = d[j].mean(), d[k].mean()
            vx, vy = ex*(1-ex), ey*(1-ey)
            if vx < 1e-12 or vy < 1e-12:
                corrs.append(0.0)
            else:
                corrs.append(abs((np.mean(d[j]*d[k]) - ex*ey) / np.sqrt(vx*vy)))
    # Bước 5: tổng hợp
    return float(np.mean(corrs)), float(np.max(corrs))

def main():
    avg_corr, max_corr = bic(SBOX)

    print("=" * 40)
    print("  KẾT QUẢ BIC")
    print("=" * 40)
    print(f"  Tương quan trung bình : {avg_corr:.4f}")
    print(f"  Tương quan lớn nhất   : {max_corr:.4f}")
    print("=" * 40)


if __name__ == "__main__":
    main()
