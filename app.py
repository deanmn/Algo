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
    df = yf.download(symbol, period="60d", interval="1d", progress=False)
    df = df[['High', 'Low', 'Close']].dropna()
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_period).mean()
    
    latest = df.iloc[-1]
    latest_atr = atr.iloc[-1]
    pip_size = get_pip_size(symbol)
    
    return {
        'date': latest.name.strftime('%Y-%m-%d'),
        'high': float(latest['High']),
        'low': float(latest['Low']),
        'atr_pips': round(float(latest_atr) / pip_size),
        'pip_size': pip_size,
        'symbol': symbol
    }

def calculate_levels(high, low, atr_pips, pip_size=0.0001):
    atr_value = atr_pips * pip_size
    
    # LONG
    long_entry = high
    long_target = high + (0.92 * atr_value)
    long_stop = low + (5.0 * pip_size)
    
    # SHORT
    short_entry = low
    short_target = low - (0.92 * atr_value)
    short_stop = high - (5.0 * pip_size)
    
    # LONG Section
    st.subheader("🟢 LONG Trade")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entry", f"{long_entry:.4f}")
    col2.metric("Target", f"{long_target:.4f}")
    col3.metric("Stop Loss", f"{long_stop:.4f}")
    
    # SHORT Section
    st.subheader("🔴 SHORT Trade")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entry", f"{short_entry:.4f}")
    col2.metric("Target", f"{short_target:.4f}")
    col3.metric("Stop Loss", f"{short_stop:.4f}")

# Main button
if st.button("🔄 Get Today's Levels", type="primary"):
    with st.spinner("Fetching latest market data..."):
        try:
            yf_symbol = pairs[selected_pair]
            data = get_previous_day_levels(yf_symbol)
            
            st.success(f"✅ **{selected_pair}** — Previous Day: **{data['date']}**")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("High", f"{data['high']:.4f}")
            col2.metric("Low", f"{data['low']:.4f}")
            col3.metric("ATR(20)", f"{data['atr_pips']} pips")
            
            calculate_levels(data['high'], data['low'], data['atr_pips'], data['pip_size'])
            
        except Exception as e:
            st.error(f"Error fetching data: {e}\n\nTry again after 4 PM ET (market close).")

st.info("💡 Add this page to your home screen for quick access")
