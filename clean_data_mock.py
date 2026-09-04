import numpy as np
import pandas as pd

# Giả lập dữ liệu đã qua xử lý của Subteam 1
np.random.seed(42)
dates = pd.date_range(end='2026-09-03', periods=100, freq='D')
tickers_exchanges = [
    ('AAA', 'HOSE'),
    ('SSI', 'HOSE'),
    ('CEO', 'HNX'),
    ('BSR', 'UPCOM'),
]

data = []
for ticker, exchange in tickers_exchanges:
    base_price = np.random.randint(10, 50)
    prices = base_price + np.cumsum(np.random.randn(100) * 0.5)
    for i in range(100):
        data.append({
            'Ticker': ticker,
            'Exchange': exchange,
            'TradingDate': dates[i],
            'Open': round(prices[i] - 0.2, 2),
            'High': round(prices[i] + 0.5, 2),
            'Low': round(prices[i] - 0.5, 2),
            'Close': round(prices[i], 2),
            'Volume': np.random.randint(10000, 500000),
        })

df_clean = pd.DataFrame(data)
df_clean.to_csv('cleaned_stock_data.csv', index=False)
print(
    "Đã tạo file dữ liệu mẫu đã làm sạch: 'cleaned_stock_data.csv' (Giả lập kết quả Subteam 1)"
)