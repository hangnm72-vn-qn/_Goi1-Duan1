import numpy as np
import pandas as pd


# ==============================================================================
# 1. HÀM TÍNH TOÁN CÁC CHỈ BÁO KỸ THUẬT (TECHNICAL INDICATORS)
# ==============================================================================
def add_technical_indicators(df):
    """Tính toán các chỉ báo kỹ thuật cơ bản và nâng cao cho chuỗi thời gian cổ phiếu.

    Input : DataFrame chứa các cột [<Ticker>, <Date>, <Open>, <High>, <Low>,
    <Close>, <Volume>]
    Output: DataFrame đã được bổ sung các cột chỉ báo kỹ thuật.
    """
    df = df.copy()

    # Chuẩn hóa kiểu dữ liệu và sắp xếp chuỗi thời gian
    df["<Date>"] = pd.to_datetime(df["<Date>"])
    df = df.sort_values(by=["<Ticker>", "<Date>"]).reset_index(drop=True)

    # Nhóm theo từng mã cổ phiếu để tính toán độc lập
    gb_close = df.groupby("<Ticker>")["<Close>"]
    gb_volume = df.groupby("<Ticker>")["<Volume>"]

    # --------------------------------------------------------------------------
    # A. CÁC ĐƯỜNG TRUNG BÌNH ĐỘNG (MOVING AVERAGES)
    # --------------------------------------------------------------------------
    # SMA 20, SMA 50, SMA 200
    df["SMA_20"] = gb_close.transform(
        lambda x: x.rolling(window=20, min_periods=20).mean()
    )
    df["SMA_50"] = gb_close.transform(
        lambda x: x.rolling(window=50, min_periods=50).mean()
    )
    df["SMA_200"] = gb_close.transform(
        lambda x: x.rolling(window=200, min_periods=200).mean()
    )

    # EMA 12, EMA 26
    df["EMA_12"] = gb_close.transform(
        lambda x: x.ewm(span=12, adjust=False).mean()
    )
    df["EMA_26"] = gb_close.transform(
        lambda x: x.ewm(span=26, adjust=False).mean()
    )

    # --------------------------------------------------------------------------
    # B. CHỈ BÁO ĐỘNG LƯỢNG (RSI - RELATIVE STRENGTH INDEX 14)
    # --------------------------------------------------------------------------
    def calc_rsi(series, period=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    df["RSI_14"] = gb_close.transform(calc_rsi)

    # --------------------------------------------------------------------------
    # C. CHỈ BÁO MACD (MOVING AVERAGE CONVERGENCE DIVERGENCE 12, 26, 9)
    # --------------------------------------------------------------------------
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df.groupby("<Ticker>")["MACD"].transform(
        lambda x: x.ewm(span=9, adjust=False).mean()
    )
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # --------------------------------------------------------------------------
    # D. DẢI BOLLINGER BANDS (20, 2)
    # --------------------------------------------------------------------------
    std_20 = gb_close.transform(
        lambda x: x.rolling(window=20, min_periods=20).std()
    )
    df["BB_Middle"] = df["SMA_20"]
    df["BB_Upper"] = df["BB_Middle"] + (std_20 * 2)
    df["BB_Lower"] = df["BB_Middle"] - (std_20 * 2)

    # --------------------------------------------------------------------------
    # E. KHỐI LƯỢNG TRUNG BÌNH DỘNG (VOLUME MA 20) & ĐỘ TĂNG KHỐI LƯỢNG
    # --------------------------------------------------------------------------
    df["Volume_MA20"] = gb_volume.transform(
        lambda x: x.rolling(window=20, min_periods=20).mean()
    )
    df["Volume_Ratio"] = df["<Volume>"] / df["Volume_MA20"].replace(0, np.nan)

    return df


# ==============================================================================
# 2. THUẬT TOÁN ĐỊNH LƯỢNG GÁN TÍN HIỆU MUA / BÁN (TRADING STRATEGY)
# ==============================================================================
def generate_trading_signals(df):
    """Thiết lập logic thuật toán Mua/Bán dựa trên sự kết hợp các chỉ báo.

    - Tín hiệu MUA (BUY): RSI vùng quá bán/tích lũy (<45) + Giá nằm trên SMA50 +
    MACD cắt lên Signal.
    - Tín hiệu BÁN (SELL): RSI vùng quá mua (>65) HOẶC MACD cắt xuống Signal.
    - Tín hiệu NẮM GIỮ (HOLD): Các trường hợp còn lại.
    """
    df = df.copy()

    # Khởi tạo mặc định
    df["Signal"] = "HOLD"
    df["Indicator"] = "None"

    # Điều kiện MUA (BUY Condition)
    buy_condition = (
        (df["RSI_14"] < 45)
        & (df["<Close>"] > df["SMA_50"])
        & (df["MACD"] > df["MACD_Signal"])
    )

    # Điều kiện BÁN (SELL Condition)
    sell_condition = (df["RSI_14"] > 65) | (df["MACD"] < df["MACD_Signal"])

    # Gán kết quả
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
        # Đọc thử file dữ liệu sạch từ Nhiệm vụ 2
        test_df = pd.read_csv("cleaned_stock_data.csv")
        print(f"✓ Đã đọc file dữ liệu: {len(test_df):,} dòng")

        # 1. Test tính chỉ báo
        df_with_indicators = add_technical_indicators(test_df)
        print("✓ Tính toán các chỉ báo kỹ thuật thành công!")

        # 2. Test gán tín hiệu chiến lược
        df_final = generate_trading_signals(df_with_indicators)
        print("✓ Gán tín hiệu chiến lược Mua/Bán thành công!")

        # In mẫu 5 dòng kết quả
        sample_cols = [
            "<Ticker>",
            "<Date>",
            "<Close>",
            "SMA_50",
            "RSI_14",
            "MACD",
            "Signal",
            "Indicator",
        ]
        print("\nMẫu kết quả phân tích:")
        print(df_final[sample_cols].tail(5).to_string(index=False))

    except Exception as e:
        print(f"❌ Lỗi khi kiểm thử: {e}")