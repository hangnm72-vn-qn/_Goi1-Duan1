# =========================================================
# THÔNG TIN THỰC HIỆN DỰ ÁN
# Nền tảng Phân tích & Sàng lọc Cổ phiếu Tự động
# ---------------------------------------------------------
# Thành viên thực hiện:
# 1. Huỳnh Thị Thúy Kiều - K244141624
# 2. Nguyễn Minh Hằng  - K244141608 
# 3. Trần Thị Bảo Hà  - K244141606
# 4. Trần Hoàng Bảo Ân  - K244141598
#5. Trương Thị Khánh Hưng - K244141619
# 6. Trần Hoàng Hương Giang - K244141604
# =========================================================
import os
import subprocess
import sys
from pathlib import Path


def run_pipeline():
    print("============================================================")
    print("🚀 HE THONG PHAN TICH CHUNG KHOAN TU DONG (FULL PIPELINE)")
    print("============================================================\n")

    base_dir = Path(__file__).resolve().parent
    src_dir = base_dir / "stock_analytics" / "src"

    # 1. BƯỚC 1: XỬ LÝ VÀ LÀM SẠCH DỮ LIỆU
    print("[1/3] Đang thực hiện Pipeline làm sạch dữ liệu (data_cleaner.py)...")
    cleaner_script = src_dir / "data_cleaner.py"
    if cleaner_script.exists():
        res1 = subprocess.run([sys.executable, str(cleaner_script)])
        if res1.returncode != 0:
            print("❌ Lỗi ở bước Làm sạch dữ liệu. Dừng pipeline!")
            return
    else:
        print(f"⚠️ Không tìm thấy script: {cleaner_script}")

    # 2. BƯỚC 2: TÍNH CHỈ BÁO & LỌC CỔ PHIẾU (SCREENER)
    print("\n[2/3] Đang thực hiện Engine phân tích & Screener (screener.py)...")
    screener_script = src_dir / "screener.py"
    if screener_script.exists():
        res2 = subprocess.run([sys.executable, str(screener_script)])
        if res2.returncode != 0:
            print("❌ Lỗi ở bước Screener. Dừng pipeline!")
            return
    else:
        print(f"⚠️ Không tìm thấy script: {screener_script}")

    # 3. BƯỚC 3: KHỞI CHẠY GIAO DIỆN STREAMLIT DASHBOARD
    print("\n[3/3] Đang khởi chạy Giao diện Dashboard (app_ui.py)...")
    ui_script = src_dir / "app_ui.py"
    if ui_script.exists():
        print("🌐 Mở trình duyệt tại địa chỉ: http://localhost:8501\n")
        subprocess.run(["streamlit", "run", str(ui_script)])
    else:
        print(f"❌ Không tìm thấy script UI: {ui_script}")


if __name__ == "__main__":
    run_pipeline()