import os
import sqlite3
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Thêm đường dẫn thư mục src vào sys.path để import các module nội bộ
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

# Import module tính toán chỉ báo và bộ lọc cổ phiếu
from indicators import add_technical_indicators
from screener import run_screener

# ==========================================
# 1. CẤU HÌNH TRANG DASHBOARD
# ==========================================
st.set_page_config(
    page_title="Hệ thống Phân tích & Sàng lọc Cổ phiếu",
    page_icon="📈",
    layout="wide",
)
st.title("📈 HỆ THỐNG PHÂN TÍCH VÀ SÀNG LỌC CỔ PHIẾU TỰ ĐỘNG")

# Định vị đường dẫn dữ liệu
BASE_DIR = SRC_DIR.parent
DB_PATH = BASE_DIR / "data" / "database" / "stock_database.db"
CSV_PATH = BASE_DIR / "data" / "processed" / "cleaned_stock_data.csv"

# Đường dẫn dự phòng
if not DB_PATH.exists():
    DB_PATH = BASE_DIR / "data" / "stock_database.db"
if not CSV_PATH.exists():
    CSV_PATH = BASE_DIR / "data" / "cleaned_stock_data.csv"


# ==========================================
# 2. HÀM TẢI DỮ LIỆU THỰC TỪ CSDL & SCREENER
# ==========================================
@st.cache_data
def load_real_data():
    """Tải dữ liệu giá lịch sử từ CSDL SQLite và chạy Screener lấy kết quả lọc thực tế"""
    df_price = pd.DataFrame()
    df_screener = pd.DataFrame()

    # 1. Tải dữ liệu lịch sử giá
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            df_price = pd.read_sql("SELECT * FROM stock_prices", conn)
            conn.close()
        except Exception as e:
            st.error(f"Lỗi kết nối CSDL SQLite: {e}")

    # Dự phòng đọc CSV nếu SQLite chưa nạp được
    if df_price.empty and CSV_PATH.exists():
        df_price = pd.read_csv(CSV_PATH)

    # Chuẩn hóa tên cột và kiểu dữ liệu
    if not df_price.empty:
        df_price.columns = [
            str(c).replace("<", "").replace(">", "").strip()
            for c in df_price.columns
        ]
        if "Date" in df_price.columns:
            df_price["Date"] = pd.to_datetime(df_price["Date"])
            df_price = df_price.sort_values("Date")

    # 2. Gọi Screener thực tế để lọc tín hiệu toàn thị trường
    try:
        df_screener = run_screener()
    except Exception as e:
        st.warning(f"Chưa thể tải dữ liệu Screener: {e}")

    return df_price, df_screener


# Nạp dữ liệu thực tế
df_price, df_screener = load_real_data()

if df_price.empty:
    st.error(
        "⚠️ Chưa tìm thấy dữ liệu! Vui lòng chạy lệnh `python stock_analytics/src/data_cleaner.py` ở Terminal trước."
    )
    st.stop()

# ==========================================
# 3. SIDEBAR TƯƠNG TÁC LỌC CỔ PHIẾU
# ==========================================
st.sidebar.header("🔍 Tùy chọn Phân tích")

# Lựa chọn Sàn giao dịch
exchanges = (
    ["TẤT CẢ"] + sorted(df_price["Exchange"].dropna().unique().tolist())
    if "Exchange" in df_price.columns
    else ["TẤT CẢ"]
)
selected_exchange = st.sidebar.selectbox("Sàn giao dịch", exchanges)

# Lọc danh sách mã cổ phiếu theo Sàn
if selected_exchange != "TẤT CẢ" and "Exchange" in df_price.columns:
    available_tickers = sorted(
        df_price[df_price["Exchange"] == selected_exchange]["Ticker"]
        .unique()
        .tolist()
    )
else:
    available_tickers = sorted(df_price["Ticker"].unique().tolist())

# Chọn Mã cổ phiếu mặc định
default_index = 0
for target in ["SSI", "FPT", "AAA", "VNM", "VCB"]:
    if target in available_tickers:
        default_index = available_tickers.index(target)
        break

selected_ticker = st.sidebar.selectbox(
    "Mã cổ phiếu", available_tickers, index=default_index
)

# Lọc chuỗi dữ liệu cho mã CP được chọn và tính chỉ báo kỹ thuật
ticker_data = df_price[df_price["Ticker"] == selected_ticker].copy()
ticker_data = add_technical_indicators(ticker_data)

# Bộ lọc Khoảng thời gian
min_date = ticker_data["Date"].min().date()
max_date = ticker_data["Date"].max().date()
date_range = st.sidebar.date_input(
    "Khoảng thời gian quan sát", [min_date, max_date]
)

if len(date_range) == 2:
    start_date, end_date = date_range
    ticker_data = ticker_data[
        (ticker_data["Date"].dt.date >= start_date)
        & (ticker_data["Date"].dt.date <= end_date)
    ]

# ==========================================
# 4. METRICS THÔNG TIN THỊ TRƯỜNG Real-time
# ==========================================
st.subheader(f"📊 Thông tin thị trường: {selected_ticker}")

if not ticker_data.empty:
    latest_row = ticker_data.iloc[-1]
    prev_close = (
        ticker_data.iloc[-2]["Close"]
        if len(ticker_data) > 1
        else latest_row["Close"]
    )

    latest_close = latest_row["Close"]
    change_val = latest_close - prev_close
    change_pct = (change_val / prev_close) * 100 if prev_close != 0 else 0

    vol = latest_row["Volume"]
    vol_str = f"{vol / 1e6:.2f} Triệu" if vol >= 1e6 else f"{vol:,.0f}"

    max_price = ticker_data["High"].max()
    min_price = ticker_data["Low"].min()

    # Giá trị RSI
    rsi_val = (
        f"{latest_row['RSI_14']:.1f}"
        if "RSI_14" in latest_row and pd.notnull(latest_row["RSI_14"])
        else "N/A"
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        label="Giá gần nhất",
        value=f"{latest_close:,.2f}",
        delta=f"{change_val:+.2f} ({change_pct:+.2f}%)",
    )
    col2.metric(label="Khối lượng (Vol)", value=vol_str)
    col3.metric(label="Giá Cao nhất (Max)", value=f"{max_price:,.2f}")
    col4.metric(label="Giá Thấp nhất (Min)", value=f"{min_price:,.2f}")
    col5.metric(label="RSI (14)", value=rsi_val)

st.markdown("---")

# ==========================================
# 5. KHU VỰC BIỂU ĐỒ KỸ THUẬT PLOTLY
# ==========================================
st.subheader(f"📉 Biểu đồ Kỹ thuật Tương tác ({selected_ticker})")

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.55, 0.20, 0.25],
    subplot_titles=(
        "Nến Nhật & Dải Bollinger Bands / SMA",
        "Khối lượng giao dịch",
        "Chỉ báo MACD & RSI",
    ),
)

# 1. Nến Nhật (Candlestick)
fig.add_trace(
    go.Candlestick(
        x=ticker_data["Date"],
        open=ticker_data["Open"],
        high=ticker_data["High"],
        low=ticker_data["Low"],
        close=ticker_data["Close"],
        name="Giá CP",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ),
    row=1,
    col=1,
)

# Thêm đường SMA_20 & SMA_50
if "SMA_20" in ticker_data.columns:
    fig.add_trace(
        go.Scatter(
            x=ticker_data["Date"],
            y=ticker_data["SMA_20"],
            name="SMA 20",
            line=dict(color="#ff9800", width=1.5),
        ),
        row=1,
        col=1,
    )
if "SMA_50" in ticker_data.columns:
    fig.add_trace(
        go.Scatter(
            x=ticker_data["Date"],
            y=ticker_data["SMA_50"],
            name="SMA 50",
            line=dict(color="#2196f3", width=1.5),
        ),
        row=1,
        col=1,
    )

# 2. Cột Khối lượng Giao dịch
fig.add_trace(
    go.Bar(
        x=ticker_data["Date"],
        y=ticker_data["Volume"],
        name="Khối lượng",
        marker_color="#7986cb",
    ),
    row=2,
    col=1,
)

# 3. Chỉ báo MACD
if "MACD" in ticker_data.columns and "MACD_Signal" in ticker_data.columns:
    fig.add_trace(
        go.Scatter(
            x=ticker_data["Date"],
            y=ticker_data["MACD"],
            name="MACD",
            line=dict(color="#00e676", width=1.5),
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=ticker_data["Date"],
            y=ticker_data["MACD_Signal"],
            name="Signal",
            line=dict(color="#ff5252", width=1.5),
        ),
        row=3,
        col=1,
    )

fig.update_layout(
    template="plotly_white",
    xaxis_rangeslider_visible=False,
    height=650,
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
    ),
)

fig.update_yaxes(title_text="Giá", row=1, col=1)
fig.update_yaxes(title_text="Khối lượng", row=2, col=1)
fig.update_yaxes(title_text="MACD", row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# 6. BẢNG KẾT QUẢ LỌC TÍN HIỆU CỔ PHIẾU
# ==========================================
st.subheader("🎯 Bảng kết quả sàng lọc cổ phiếu (Toàn thị trường)")

if not df_screener.empty:
    col_filter, col_search = st.columns([2, 2])

    with col_filter:
        signal_filter = st.radio(
            "Lọc theo Tín hiệu:",
            ["TẤT CẢ", "BUY", "SELL", "HOLD"],
            horizontal=True,
        )

    with col_search:
        search_ticker = st.text_input(
            "🔎 Tìm kiếm Mã cổ phiếu:", value=""
        ).upper()

    # Lọc dữ liệu hiển thị
    filtered_df = df_screener.copy()

    if signal_filter != "TẤT CẢ":
        filtered_df = filtered_df[filtered_df["Signal"] == signal_filter]

    if search_ticker:
        filtered_df = filtered_df[
            filtered_df["Ticker"].str.contains(search_ticker, na=False)
        ]

    # Hàm tô màu định dạng tín hiệu
    def color_signals(val):
        if val == "BUY":
            return "background-color: #d4edda; color: #155724; font-weight: bold"
        elif val == "SELL":
            return "background-color: #f8d7da; color: #721c24; font-weight: bold"
        return "background-color: #fff3cd; color: #856404"

    # Đổi tên cột hiển thị thân thiện hơn
    rename_dict = {
        "Ticker": "Mã CP",
        "Exchange": "Sàn",
        "Close": "Giá đóng cửa",
        "Signal": "Tín hiệu",
        "Indicator": "Chỉ báo tạo tín hiệu",
        "Signal Date": "Ngày phát tín hiệu",
    }
    display_df = filtered_df.rename(columns=rename_dict)

    signal_col = "Tín hiệu" if "Tín hiệu" in display_df.columns else "Signal"

    st.dataframe(
        display_df.style.map(color_signals, subset=[signal_col]),
        use_container_width=True,
        height=400,
    )
else:
    st.info(
        "Chưa có dữ liệu sàng lọc. Vui lòng kiểm tra lại file `screener.py`."
    )