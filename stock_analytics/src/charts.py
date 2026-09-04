import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def plot_stock_technical_chart(ticker_data, ticker_symbol="Cổ phiếu"):
    """
    Vẽ Biểu đồ Kỹ thuật Nâng cao tương tác (Candlestick + Volume + SMA + MACD) bằng Plotly.
    """
    if ticker_data.empty:
        return None

    # Khởi tạo Subplots: Row 1 (Giá + SMA), Row 2 (Volume), Row 3 (MACD)
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.55, 0.20, 0.25],
        subplot_titles=(
            f"Diễn biến Giá & Các đường Trung bình ({ticker_symbol})",
            "Khối lượng Giao dịch",
            "Chỉ báo Động lượng MACD",
        ),
    )

    # 1. Biểu đồ Nến Nhật (Candlestick)
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

    # Các đường SMA (Trung bình động)
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

    # 2. Biểu đồ Khối lượng (Volume)
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
                name="MACD Signal",
                line=dict(color="#ff5252", width=1.5),
            ),
            row=3,
            col=1,
        )

    # Cấu hình giao diện biểu đồ
    fig.update_layout(
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        height=700,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_yaxes(title_text="Giá (VNĐ)", row=1, col=1)
    fig.update_yaxes(title_text="Khối lượng", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    return fig


if __name__ == "__main__":
    print("✓ Module charts.py đã khởi tạo thành công!")