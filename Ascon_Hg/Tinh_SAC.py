import numpy as np
import matplotlib.pyplot as plt

# S-box Ascon (5-bit)
def sbox_ascon(x):
    sbox_table = [
        0x04, 0x0b, 0x1f, 0x14, 0x1a, 0x15, 0x09, 0x02,
        0x1b, 0x05, 0x08, 0x12, 0x1d, 0x03, 0x06, 0x1c,
        0x1e, 0x13, 0x07, 0x0e, 0x00, 0x0d, 0x11, 0x18,
        0x10, 0x0c, 0x01, 0x19, 0x16, 0x0a, 0x0f, 0x17,
    ]
    return sbox_table[x]

def calculate_sac_matrix(sbox_func, n_bits=5):
    """
    Tính toán Ma trận SAC (Dependency Matrix)
    Hàng i: Bit đầu vào bị đảo
    Cột j: Bit đầu ra bị thay đổi
    """
    size = 2**n_bits
    # Khởi tạo ma trận đếm sự thay đổi (5x5)
    dependency_matrix = np.zeros((n_bits, n_bits))

    for x in range(size):
        y = sbox_func(x)
        for i in range(n_bits):
            # Đảo bit thứ i của đầu vào
            x_prime = x ^ (1 << i)
            y_prime = sbox_func(x_prime)
            
            # Tính toán sự khác biệt đầu ra (XOR)
            diff = y ^ y_prime
            
            for j in range(n_bits):
                # Nếu bit thứ j của đầu ra thay đổi, tăng biến đếm
                if (diff >> j) & 1:
                    dependency_matrix[i][j] += 1

    # Chia cho tổng số đầu vào để ra xác suất
    sac_matrix = dependency_matrix / size
    return sac_matrix

def plot_sac_heatmap(matrix):
    """ Vẽ heatmap của ma trận SAC """
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix, cmap='YlOrRd', interpolation='nearest', vmin=0, vmax=1)
    plt.colorbar(label='Xác suất thay đổi (Lý tưởng = 0.5)')
    
    n = matrix.shape[0]
    plt.xticks(range(n), [f'Out {i}' for i in range(n)])
    plt.yticks(range(n), [f'In {i}' for i in range(n)])
    
    # Hiển thị giá trị số lên từng ô
    for i in range(n):
        for j in range(n):
            plt.text(j, i, f'{matrix[i, j]:.3f}', ha='center', va='center', color='black')

    plt.title('Ma trận Tiêu chuẩn Thác chặt (SAC) - Ascon S-box')
    plt.xlabel('Vị trí bit đầu ra')
    plt.ylabel('Vị trí bit đầu vào bị đảo')
    plt.show()

def main():
    # --- THỰC THI VÀ TÍNH TOÁN ---
    n_bits = 5
    sac_results = calculate_sac_matrix(sbox_ascon, n_bits)

    # Tính toán các chỉ số sai lệch (Deviation)
    # Sai lệch là trị tuyệt đối của (Xác suất thực tế - 0.5)
    deviations = np.abs(sac_results - 0.5)
    avg_dev = np.mean(deviations)
    max_dev = np.max(deviations)

    # In kết quả báo cáo
    print("=" * 50)
    print("PHÂN TÍCH TIÊU CHUẨN THÁC CHẶT (SAC) CHO S-BOX")
    print("=" * 50)
    print("Ma trận xác suất (Dependency Matrix):")
    print(sac_results)
    print("-" * 50)
    print(f"Sai lệch trung bình (Average Deviation): {avg_dev:.4f}")
    print(f"Sai lệch lớn nhất (Max Deviation):         {max_dev:.4f}")
    print("=" * 50)
    print("Ghi chú: Sai lệch càng gần 0, S-box càng thỏa mãn SAC tốt.")
    # Vẽ biểu đồ
    plot_sac_heatmap(sac_results)


if __name__ == "__main__":
    main()
