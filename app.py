import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="ATR 20 Levels", layout="centered", initial_sidebar_state="collapsed")

st.title("📈 Daily ATR(20) Levels")
st.caption("Previous Day's High/Low as Entry • Refresh after 4 PM ET")

# Available pairs
pairs = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X"
}

selected_pair = st.selectbox("Select Currency Pair", options=list(pairs.keys()))

def get_pip_size(symbol):
    return 0.01 if "JPY" in symbol else 0.0001

def get_previous_day_levels(symbol: str, atr_period: int = 20):
    # Use Ticker().history() — always returns clean columns, no MultiIndex issues
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="60d", interval="1d")
    df = df[['High', 'Low', 'Close']].dropna()

    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_period).mean()

    latest_high = float(df['High'].values[-1])
    latest_low = float(df['Low'].values[-1])
    latest_atr = float(atr.values[-1])
    latest_date = df.index[-1].strftime('%Y-%m-%d')
    pip_size = get_pip_size(symbol)

    return {
        'date': latest_date,
        'high': latest_high,
        'low': latest_low,
        'atr_pips': round(latest_atr / pip_size),
        'pip_size': pip_size,
        'symbol': symbol
    }

def calculate_levels(high, low, atr_pips, pip_size=0.0001):
    atr_value = atr_pips * pip_size
    fmt = ".2f" if pip_size == 0.01 else ".4f"

    long_entry = high
    long_target = high + (0.92 * atr_value)
    long_stop = low + (5.0 * pip_size)

    short_entry = low
    short_target = low - (0.92 * atr_value)
    short_stop = high - (5.0 * pip_size)

    st.subheader("🟢 LONG Trade")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entry", f"{long_entry:{fmt}}")
    col2.metric("Target", f"{long_target:{fmt}}")
    col3.metric("Stop Loss", f"{long_stop:{fmt}}")

    st.subheader("🔴 SHORT Trade")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entry", f"{short_entry:{fmt}}")
    col2.metric("Target", f"{short_target:{fmt}}")
    col3.metric("Stop Loss", f"{short_stop:{fmt}}")

if st.button("🔄 Get Today's Levels", type="primary"):
    with st.spinner("Fetching latest market data..."):
        try:
            yf_symbol = pairs[selected_pair]
            data = get_previous_day_levels(yf_symbol)

            st.success(f"✅ **{selected_pair}** — Previous Day: **{data['date']}**")

            fmt = ".2f" if data['pip_size'] == 0.01 else ".4f"

            col1, col2, col3 = st.columns(3)
            col1.metric("High", f"{data['high']:{fmt}}")
            col2.metric("Low", f"{data['low']:{fmt}}")
            col3.metric("ATR(20)", f"{data['atr_pips']} pips")

            calculate_levels(data['high'], data['low'], data['atr_pips'], data['pip_size'])

        except Exception as e:
            st.error(f"Error fetching data: {e}\n\nTry again after 4 PM ET (market close).")

st.info("💡 Add this page to your home screen for quick access")
