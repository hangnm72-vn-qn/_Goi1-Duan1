import os
import sys
from pathlib import Path
import pandas as pd

# Thêm thư mục src vào hệ thống import để tránh lỗi ModuleNotFoundError
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from indicators import add_technical_indicators, generate_trading_signals


def run_screener(input_file="stock_analytics/data/processed/cleaned_stock_data.csv"):
    """
    Module Screener:
    - Nạp dữ liệu đã làm sạch
    - Tính chỉ báo kỹ thuật & Tín hiệu Mua/Bán
    - Lọc phiên giao dịch mới nhất cho từng mã cổ phiếu
    """
    # Danh sách các đường dẫn dự phòng
    possible_paths = [
        input_file,
        "stock_analytics/data/processed/cleaned_stock_data.csv",
        "stock_analytics/data/cleaned_stock_data.csv",
        "cleaned_stock_data.csv",
    ]

    target_path = next((p for p in possible_paths if os.path.exists(p)), None)

    if not target_path:
        raise FileNotFoundError(
            "Không tìm thấy file cleaned_stock_data.csv! Hãy chạy data_cleaner.py trước."
        )

    print(f"🔄 [Screener] Đang nạp dữ liệu từ: {target_path}")
    df = pd.read_csv(target_path)

    # 1. Tính chỉ báo & gán tín hiệu
    df_calc = add_technical_indicators(df)
    df_sig = generate_trading_signals(df_calc)

    # 2. Lấy dữ liệu phiên mới nhất cho từng mã cổ phiếu
    latest = df_sig.groupby("Ticker").last().reset_index()

    # Chuẩn hóa cột Date
    if "Date" in latest.columns:
        latest["Signal Date"] = pd.to_datetime(latest["Date"]).dt.strftime("%Y-%m-%d")
    else:
        latest["Signal Date"] = "N/A"

    # Đảm bảo cột Exchange tồn tại
    if "Exchange" not in latest.columns:
        latest["Exchange"] = "HOSE/HNX"

    # 3. Lựa chọn các cột xuất ra bảng Screener
    selected_cols = ["Ticker", "Exchange", "Close", "Signal", "Indicator", "Signal Date"]
    available_cols = [c for c in selected_cols if c in latest.columns]

    result = latest[available_cols].copy()
    
    if "Close" in result.columns:
        result["Close"] = result["Close"].round(2)

    return result


if __name__ == "__main__":
    print("============================================================")
    print("TV4 - STOCK SCREENER")
    print("============================================================")
    try:
        screener_result = run_screener()
        print(f"✅ Đã lọc thành công {len(screener_result):,} mã cổ phiếu!\n")
        print("Mẫu 10 kết quả đầu tiên:")
        print(screener_result.head(10).to_string(index=False))
    except Exception as e:
        print(f"❌ Lỗi khi chạy Screener: {e}")