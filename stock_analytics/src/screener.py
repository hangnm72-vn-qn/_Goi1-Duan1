from indicators import add_technical_indicators, generate_trading_signals
import pandas as pd


def run_screener(input_file="stock_analytics/data/cleaned_stock_data.csv"):
    import os

    # Dự phòng nếu file CSV nằm ở gốc ngoài
    if not os.path.exists(input_file):
        input_file = "cleaned_stock_data.csv"

    df = pd.read_csv(input_file)
    # ... giữ nguyên các đoạn code còn lại phía dưới ...

    # Dùng trực tiếp hàm do Thành viên 3 viết
    df_calc = add_technical_indicators(df)
    df_sig = generate_trading_signals(df_calc)

    # Lọc phiên mới nhất
    latest = df_sig.groupby("<Ticker>").last().reset_index()
    latest["Signal Date"] = pd.to_datetime(latest["<Date>"]).dt.strftime(
        "%Y-%m-%d"
    )

    result = latest[[
        "<Ticker>",
        "Exchange",
        "<Close>",
        "Signal",
        "Indicator",
        "Signal Date",
    ]].copy()
    result = result.rename(columns={"<Ticker>": "Ticker", "<Close>": "Close"})
    result["Close"] = result["Close"].round(2)

    return result


if __name__ == "__main__":
    screener_result = run_screener()
    print(screener_result.head(10).to_string(index=False))