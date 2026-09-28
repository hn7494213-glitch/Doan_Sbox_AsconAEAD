"""
main.py - Giao diện điều khiển chính của công cụ Ascon_Hg.

Mỗi chức năng nằm trong một file .py riêng, main.py chỉ hiển thị menu
và gọi hàm main() của file tương ứng.
"""

import sys
import importlib
import traceback

# Đảm bảo in được tiếng Việt / ký tự ⊕ trên Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


MENU = """
========================================
                 Ascon_Hg
      Công cụ sinh và đánh giá S-box
========================================

1. Sinh S-box
2. Đánh giá số nhánh vi sai và tuyến tính
3. Tính SAC
4. Tính BIC
5. Tạo đầu vào cho AsconTrailTool ascnColScore1
6. Tạo đầu vào AscontrailTool asconTrail
7. Đánh giá tính đúng đắn khi thay S-Box
0. Thoát

========================================"""

# lựa chọn -> (tên module, tên chức năng)
CHUC_NANG = {
    "1": ("Sinh_SBOX", "Sinh S-box"),
    "2": ("Danhgiasobranhvisaituyentinh", "Đánh giá số nhánh vi sai và tuyến tính"),
    "3": ("Tinh_SAC", "Tính SAC"),
    "4": ("Tinh_BIC", "Tính BIC"),
    "5": ("tinhdauvaohoasconColScore1", "Tạo đầu vào cho AsconTrailTool ascnColScore1"),
    "6": ("tinhchoascontrail1", "Tạo đầu vào AscontrailTool asconTrail"),
    "7": ("ascon_AEAD_final_vn", "Đánh giá tính đúng đắn khi thay S-Box"),
}


def chay(ten_module, ten_chuc_nang):
    print(f"\n>>> {ten_chuc_nang}\n")
    try:
        # import khi cần: thiếu thư viện (numpy, matplotlib) chỉ ảnh hưởng
        # đúng chức năng dùng nó, không làm hỏng cả menu
        mod = importlib.import_module(ten_module)
        mod.main()
    except Exception:
        print("Lỗi khi chạy chức năng này:")
        traceback.print_exc()


def main():
    while True:
        print(MENU)
        chon = input("Chọn chức năng: ").strip()
        if chon == "0":
            print("Thoát Ascon_Hg.")
            break
        if chon in CHUC_NANG:
            chay(*CHUC_NANG[chon])
            input("\nNhấn Enter để quay lại menu...")
        else:
            print("Lựa chọn không hợp lệ, vui lòng nhập 0-6.")


if __name__ == "__main__":
    main()