import os
import numpy as np
import pandas as pd


def prepare_columns(df):
    """Làm sạch tên cột: Loại bỏ các dấu '<' và '>' nếu có."""
    df = df.copy()
    df.columns = [
        str(c).replace("<", "").replace(">", "").strip() for c in df.columns
    ]
    return df


# ==============================================================================
# 1. HÀM TÍNH TOÁN CÁC CHỈ BÁO KỸ THUẬT (TECHNICAL INDICATORS)
# ==============================================================================
def add_technical_indicators(df):
    """Tính toán các chỉ báo kỹ thuật cơ bản và nâng cao cho chuỗi thời gian cổ phiếu."""
    df = prepare_columns(df)

    # Chuẩn hóa kiểu dữ liệu và sắp xếp chuỗi thời gian
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by=["Ticker", "Date"]).reset_index(drop=True)

    # Nhóm theo từng mã cổ phiếu để tính toán độc lập
    gb_close = df.groupby("Ticker")["Close"]
    gb_volume = df.groupby("Ticker")["Volume"]

    # A. CÁC ĐƯỜNG TRUNG BÌNH ĐỘNG
    df["SMA_20"] = gb_close.transform(
        lambda x: x.rolling(window=20, min_periods=1).mean()
    )
    df["SMA_50"] = gb_close.transform(
        lambda x: x.rolling(window=50, min_periods=1).mean()
    )
    df["SMA_200"] = gb_close.transform(
        lambda x: x.rolling(window=200, min_periods=1).mean()
    )

    df["EMA_12"] = gb_close.transform(
        lambda x: x.ewm(span=12, adjust=False).mean()
    )
    df["EMA_26"] = gb_close.transform(
        lambda x: x.ewm(span=26, adjust=False).mean()
    )

    # B. CHỈ BÁO RSI (14)
    def calc_rsi(series, period=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    df["RSI_14"] = gb_close.transform(calc_rsi)

    # C. CHỈ BÁO MACD (12, 26, 9)
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df.groupby("Ticker")["MACD"].transform(
        lambda x: x.ewm(span=9, adjust=False).mean()
    )
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # D. DẢI BOLLINGER BANDS (20, 2)
    std_20 = gb_close.transform(
        lambda x: x.rolling(window=20, min_periods=1).std()
    )
    df["BB_Middle"] = df["SMA_20"]
    df["BB_Upper"] = df["BB_Middle"] + (std_20.fillna(0) * 2)
    df["BB_Lower"] = df["BB_Middle"] - (std_20.fillna(0) * 2)

    # E. KHỐI LƯỢNG TRUNG BÌNH DỘNG
    df["Volume_MA20"] = gb_volume.transform(
        lambda x: x.rolling(window=20, min_periods=1).mean()
    )
    df["Volume_Ratio"] = df["Volume"] / df["Volume_MA20"].replace(0, np.nan)

    return df


# ==============================================================================
# 2. THUẬT TOÁN ĐỊNH LƯỢNG GÁN TÍN HIỆU MUA / BÁN
# ==============================================================================
def generate_trading_signals(df):
    """Thiết lập logic thuật toán Mua/Bán dựa trên sự kết hợp các chỉ báo."""
    df = prepare_columns(df)

    df["Signal"] = "HOLD"
    df["Indicator"] = "None"

    buy_condition = (
        (df["RSI_14"] < 45)
        & (df["Close"] > df["SMA_50"])
        & (df["MACD"] > df["MACD_Signal"])
    )

    sell_condition = (df["RSI_14"] > 65) | (df["MACD"] < df["MACD_Signal"])

    df.loc[buy_condition, "Signal"] = "BUY"
    df.loc[buy_condition, "Indicator"] = "RSI<45 & Close>SMA50 & MACD Bullish"

    df.loc[sell_condition, "Signal"] = "SELL"
    df.loc[sell_condition, "Indicator"] = "RSI>65 or MACD Bearish"

    return df


# ==============================================================================
# KIỂM THỬ ĐỘC LẬP MODULE (UNIT TEST)
# ==============================================================================
if __name__ == "__main__":
    print("--- KIỂM THỬ MODULE INDICATORS.PY ---")
    try:
        # Đường dẫn chính xác do TV2 xuất ra
        possible_paths = [
            "stock_analytics/data/processed/cleaned_stock_data.csv",
            "stock_analytics/data/cleaned_stock_data.csv",
            "cleaned_stock_data.csv",
        ]

        target_path = next((p for p in possible_paths if os.path.exists(p)), None)

        if not target_path:
            raise FileNotFoundError(
                "Không tìm thấy file cleaned_stock_data.csv! Vui lòng chạy data_cleaner.py trước."
            )

        test_df = pd.read_csv(target_path)
        print(f"✓ Đã đọc file dữ liệu từ '{target_path}': {len(test_df):,} dòng")

        df_with_indicators = add_technical_indicators(test_df)
        print("✓ Tính toán các chỉ báo kỹ thuật thành công!")

        df_final = generate_trading_signals(df_with_indicators)
        print("✓ Gán tín hiệu chiến lược Mua/Bán thành công!")

        sample_cols = [
            "Ticker",
            "Date",
            "Close",
            "SMA_50",
            "RSI_14",
            "MACD",
            "Signal",
            "Indicator",
        ]
        available_sample_cols = [c for c in sample_cols if c in df_final.columns]
        print("\nMẫu kết quả phân tích:")
        print(df_final[available_sample_cols].tail(5).to_string(index=False))

    except Exception as e:
        print(f"❌ Lỗi khi kiểm thử: {e}")