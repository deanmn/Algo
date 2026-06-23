import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="Artemis", layout="centered", initial_sidebar_state="collapsed")
st.title("🌙 Artemis")
st.caption("Daily ATR(20) Levels • Powered by OANDA")

pairs = {
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
    "EURJPY": "EUR_JPY",
    "GBPJPY": "GBP_JPY",
}

selected_pair = st.selectbox("Select Currency Pair", options=list(pairs.keys()))

def get_pip_size(pair):
    return 0.01 if "JPY" in pair else 0.0001

def get_previous_day_levels(instrument, atr_period=20):
    api_key = st.secrets["OANDA_API_KEY"]

    url = f"https://api-fxpractice.oanda.com/v3/instruments/{instrument}/candles"

    headers = {"Authorization": f"Bearer {api_key}"}
    params  = {"count": 60, "granularity": "D", "price": "M"}

    r = requests.get(url, headers=headers, params=params, timeout=10)
    data = r.json()

    if "candles" not in data:
        raise ValueError(data.get("errorMessage", "OANDA API error — check your API key in Streamlit Secrets"))

    candles = [c for c in data["candles"] if c["complete"]]

    if len(candles) < atr_period:
        raise ValueError(f"Not enough data: only {len(candles)} completed candles returned.")

    highs  = [float(c["mid"]["h"]) for c in candles]
    lows   = [float(c["mid"]["l"]) for c in candles]
    closes = [float(c["mid"]["c"]) for c in candles]
    dates  = [c["time"][:10] for c in candles]

    df = pd.DataFrame({"high": highs, "low": lows, "close": closes}, index=dates)

    high_low   = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close  = np.abs(df["low"]  - df["close"].shift())
    tr  = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_period).mean()

    pip_size = get_pip_size(instrument.replace("_", ""))

    return {
        "date":     df.index[-1],
        "high":     float(df["high"].values[-1]),
        "low":      float(df["low"].values[-1]),
        "atr_pips": round(float(atr.values[-1]) / pip_size),
        "pip_size": pip_size,
    }

def calculate_levels(high, low, atr_pips, pip_size=0.0001):
    atr_value = atr_pips * pip_size
    fmt = ".2f" if pip_size == 0.01 else ".4f"

    long_entry  = high
    long_tp     = high + (0.92 * atr_value)
    long_sl     = low  + (5.0  * pip_size)

    short_entry = low
    short_tp    = low  - (0.92 * atr_value)
    short_sl    = high - (5.0  * pip_size)

    st.subheader("🟢 LONG Trade")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entry",       f"{long_entry:{fmt}}")
    c2.metric("Stop Loss",   f"{long_sl:{fmt}}")
    c3.metric("Take Profit", f"{long_tp:{fmt}}")

    st.subheader("🔴 SHORT Trade")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entry",       f"{short_entry:{fmt}}")
    c2.metric("Stop Loss",   f"{short_sl:{fmt}}")
    c3.metric("Take Profit", f"{short_tp:{fmt}}")

if st.button("🌙 Get Today's Levels", type="primary"):
    with st.spinner("Scanning the cosmos..."):
        try:
            data = get_previous_day_levels(pairs[selected_pair])

            st.success(f"✅ **{selected_pair}** — Previous Day: **{data['date']}**")

            calculate_levels(data["high"], data["low"], data["atr_pips"], data["pip_size"])

        except Exception as e:
            st.error(f"Error fetching data: {e}")

st.info("💡 Add Artemis to your home screen for quick access")
