import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="Artemis", layout="centered", initial_sidebar_state="collapsed")
st.title("🌙 Artemis")
st.caption("Daily ATR(20) Levels • Previous Day's High/Low as Entry • Refresh after 4 PM ET")

pairs = {
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "EURJPY": "EUR/JPY",
    "GBPJPY": "GBP/JPY",
}

selected_pair = st.selectbox("Select Currency Pair", options=list(pairs.keys()))

def get_pip_size(pair):
    return 0.01 if "JPY" in pair else 0.0001

def get_previous_day_levels(symbol, atr_period=20):
    api_key = st.secrets["TWELVE_DATA_API_KEY"]

    r = requests.get(
        "https://api.twelvedata.com/time_series",
        params={"symbol": symbol, "interval": "1day", "outputsize": 60, "apikey": api_key},
        timeout=10
    )
    data = r.json()

    if data.get("status") != "ok":
        raise ValueError(data.get("message", "API error — check your API key in Streamlit Secrets"))

    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    df = df[["high", "low", "close"]].apply(pd.to_numeric)

    high_low   = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close  = np.abs(df["low"]  - df["close"].shift())
    tr  = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_period).mean()

    pip_size = get_pip_size(symbol.replace("/", ""))

    return {
        "date":     df.index[-1].strftime("%Y-%m-%d"),
        "high":     float(df["high"].values[-1]),
        "low":      float(df["low"].values[-1]),
        "atr_pips": round(float(atr.values[-1]) / pip_size),
        "pip_size": pip_size,
    }

def calculate_levels(high, low, atr_pips, pip_size=0.0001):
    atr_value = atr_pips * pip_size
    fmt = ".2f" if pip_size == 0.01 else ".4f"

    long_entry  = high
    long_target = high + (0.92 * atr_value)
    long_stop   = low  + (5.0  * pip_size)

    short_entry  = low
    short_target = low  - (0.92 * atr_value)
    short_stop   = high - (5.0  * pip_size)

    st.subheader("🟢 LONG Trade")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entry",     f"{long_entry:{fmt}}")
    c2.metric("Target",    f"{long_target:{fmt}}")
    c3.metric("Stop Loss", f"{long_stop:{fmt}}")

    st.subheader("🔴 SHORT Trade")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entry",     f"{short_entry:{fmt}}")
    c2.metric("Target",    f"{short_target:{fmt}}")
    c3.metric("Stop Loss", f"{short_stop:{fmt}}")

if st.button("🌙 Get Today's Levels", type="primary"):
    with st.spinner("Scanning the cosmos..."):
        try:
            data = get_previous_day_levels(pairs[selected_pair])

            st.success(f"✅ **{selected_pair}** — Previous Day: **{data['date']}**")
            fmt = ".2f" if data["pip_size"] == 0.01 else ".4f"

            c1, c2, c3 = st.columns(3)
            c1.metric("High",    f"{data['high']:{fmt}}")
            c2.metric("Low",     f"{data['low']:{fmt}}")
            c3.metric("ATR(20)", f"{data['atr_pips']} pips")

            calculate_levels(data["high"], data["low"], data["atr_pips"], data["pip_size"])

        except Exception as e:
            st.error(f"Error fetching data: {e}")

st.info("💡 Add Artemis to your home screen for quick access")
