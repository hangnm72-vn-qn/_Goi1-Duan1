import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from pathlib import Path

# ==========================================
# 1. CẤU HÌNH TRANG DASHBOARD
# ==========================================
st.set_page_config(page_title="Nền tảng Phân tích Chứng khoán", layout="wide")
st.title("📈 HỆ THỐNG PHÂN TÍCH VÀ SÀNG LỌC CỔ PHIẾU TỰ ĐỘNG")

# Xác định đường dẫn Database của Sub-team 1
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "database" / "stock_database.db"

# ==========================================
# 2. HÀM TẢI DỮ LIỆU
# ==========================================
@st.cache_data
def load_mock_price_data():
    """Dữ liệu lịch sử giá mẫu"""
    dates = pd.date_range(end='2026-09-04', periods=30)
    data = {
        'Date': dates.strftime('%Y-%m-%d'),
        'Open': [31500 + i*100 + (i%3)*50 for i in range(30)],
        'High': [32000 + i*100 + (i%2)*100 for i in range(30)],
        'Low': [31000 + i*100 - (i%3)*50 for i in range(30)],
        'Close': [31800 + i*100 + (i%4)*40 for i in range(30)],
        'Volume': [10000000 + (i%5)*1500000 for i in range(30)]
    }
    return pd.DataFrame(data)

@st.cache_data
def load_mock_screener_data():
    """Dữ liệu bảng lọc cổ phiếu mẫu"""
    data = {
        'Mã CP': ['SSI', 'HPG', 'VNM', 'VHM', 'TCB'],
        'Sàn': ['HOSE', 'HOSE', 'HOSE', 'HOSE', 'HOSE'],
        'Giá đóng cửa': [32500, 27800, 68000, 42000, 35100],
        'Tín hiệu': ['MUA', 'GIỮ', 'MUA', 'BÁN', 'GIỮ'],
        'Chỉ báo tạo tín hiệu': ['RSI Quá bán + SMA Crossover', 'Theo xu hướng', 'MACD Cắt lên', 'RSI Quá mua', 'Trung tính'],
        'Ngày phát tín hiệu': ['2026-09-03', '2026-09-03', '2026-09-03', '2026-09-03', '2026-09-03']
    }
    return pd.DataFrame(data)

# Đọc dữ liệu (Tự động chuyển từ dữ liệu giả sang DB thật khi có file)
if DB_PATH.exists():
    try:
        conn = sqlite3.connect(DB_PATH)
        df_price = pd.read_sql("SELECT * FROM stock_price", conn)
        conn.close()
    except Exception:
        df_price = load_mock_price_data()
else:
    df_price = load_mock_price_data()

df_screener = load_mock_screener_data()

# ==========================================
# 3. LỌC CỔ PHIẾU (SIDEBAR)
# ==========================================
st.sidebar.header("🔍 Lựa chọn Cổ phiếu")
selected_exchange = st.sidebar.selectbox("Sàn giao dịch", ["TẤT CẢ", "HOSE", "HNX", "UPCOM"])
selected_ticker = st.sidebar.selectbox("Mã cổ phiếu", ["SSI", "HPG", "VNM", "VIC", "FPT"])
date_range = st.sidebar.date_input("Khoảng thời gian quan sát", [pd.to_datetime("2026-08-01"), pd.to_datetime("2026-09-04")])

# ==========================================
# 4. THÔNG TIN THỊ TRƯỜNG (METRICS)
# ==========================================
st.subheader(f"📊 Thông tin thị trường: {selected_ticker}")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(label="Giá gần nhất", value="32,500 VNĐ", delta="+2.35%")
col2.metric(label="Khối lượng (Vol)", value="12.5 Triệu")
col3.metric(label="Giá Cao nhất (Max)", value="33,100 VNĐ")
col4.metric(label="Giá Thấp nhất (Min)", value="31,800 VNĐ")
col5.metric(label="RSI (14)", value="42.5", delta="Trung tính")

st.markdown("---")

# ==========================================
# 5. KHU VỰC BIỂU ĐỒ PLOTLY (TASK CỦA TV6)
# ==========================================
st.subheader("📉 Biểu đồ Kỹ thuật (Nến Nhật & Khối lượng)")

# Tạo đồ thị 2 tầng (Tầng 1: Biểu đồ nến, Tầng 2: Khối lượng giao dịch)
fig = make_subplots(
    rows=2, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.03, 
    row_heights=[0.7, 0.3]
)

# 1. Nến Nhật (Candlestick)
fig.add_trace(
    go.Candlestick(
        x=df_price['Date'],
        open=df_price['Open'],
        high=df_price['High'],
        low=df_price['Low'],
        close=df_price['Close'],
        name="Giá CP",
        increasing_line_color='#26a69a', # Nến tăng màu xanh
        decreasing_line_color='#ef5350' # Nến giảm màu đỏ
    ),
    row=1, col=1
)

# 2. Cột Khối lượng (Volume)
fig.add_trace(
    go.Bar(
        x=df_price['Date'],
        y=df_price['Volume'],
        name="Khối lượng",
        marker_color='#7986cb'
    ),
    row=2, col=1
)

# Cấu hình giao diện biểu đồ nền trắng sạch
fig.update_layout(
    template="plotly_white",
    xaxis_rangeslider_visible=False,
    height=500,
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

fig.update_yaxes(title_text="Giá (VNĐ)", row=1, col=1)
fig.update_yaxes(title_text="Khối lượng", row=2, col=1)

# Hiển thị biểu đồ Plotly lên Streamlit
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# 6. BẢNG KẾT QUẢ LỌC TÍN HIỆU CỔ PHIẾU
# ==========================================
st.subheader("🎯 Bảng kết quả lọc cổ phiếu (Tín hiệu MUA / BÁN)")

signal_filter = st.radio("Lọc theo loại tín hiệu:", ["TẤT CẢ", "MUA", "BÁN", "GIỮ"], horizontal=True)

if signal_filter != "TẤT CẢ":
    filtered_df = df_screener[df_screener['Tín hiệu'] == signal_filter]
else:
    filtered_df = df_screener

def color_signals(val):
    if val == 'MUA':
        return 'background-color: #d4edda; color: #155724; font-weight: bold'
    elif val == 'BÁN':
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
    return 'background-color: #fff3cd; color: #856404'

st.dataframe(
    filtered_df.style.map(color_signals, subset=['Tín hiệu']),
    use_container_width=True,
    height=250
)