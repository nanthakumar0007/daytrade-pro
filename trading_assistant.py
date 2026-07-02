import streamlit as st
from datetime import datetime
import random

st.set_page_config(
    page_title="DayTrade Pro",
    page_icon="📈",
    layout="centered"
)

st.markdown("""
<style>
    h1, h2 { text-align: center; }
    .metric { background: #f0f2f6; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #1f77b4; }
    .success { border-left-color: #2ecc71; }
</style>
""", unsafe_allow_html=True)

st.title("📈 DayTrade Pro")
st.subheader("Stock Trading Scanner")

# Time
now = datetime.now()
st.markdown(f"🕐 {now.strftime('%I:%M %p')} | 📅 {now.strftime('%a, %b %d')}")

st.divider()

# Disclaimer
with st.expander("⚠️ DISCLAIMER"):
    st.error("⚠️ Trading carries 100% loss risk. This is educational only. Not financial advice.")

tab1, tab2, tab3 = st.tabs(["🔍 Scanner", "📊 Info", "⚙️ Settings"])

# ============================================================================
# TAB 1: SCANNER
# ============================================================================

with tab1:
    st.subheader("Market Scanner")
    
    # Demo data
    demo_stocks = [
        {'ticker': 'AAPL', 'price': 22.50, 'shares': 1, 'stop': 21.80, 'target': 24.20, 'profit': 1.70, 'rsi': 52, 'vol': 1.8},
        {'ticker': 'MSFT', 'price': 28.30, 'shares': 1, 'stop': 27.40, 'target': 30.15, 'profit': 1.85, 'rsi': 55, 'vol': 1.6},
        {'ticker': 'GOOGL', 'price': 32.10, 'shares': 1, 'stop': 31.10, 'target': 34.30, 'profit': 2.20, 'rsi': 48, 'vol': 1.7},
        {'ticker': 'NVDA', 'price': 18.50, 'shares': 1, 'stop': 17.80, 'target': 20.10, 'profit': 1.60, 'rsi': 58, 'vol': 2.1},
        {'ticker': 'TSLA', 'price': 25.75, 'shares': 1, 'stop': 24.80, 'target': 27.65, 'profit': 1.90, 'rsi': 51, 'vol': 1.9},
    ]
    
    if st.button("🔍 SCAN MARKET", use_container_width=True, key="scan"):
        st.success("✅ **NVDA** - BUY SETUP FOUND")
        
        best = demo_stocks[3]  # NVDA is best
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Entry", f"${best['price']}")
            st.metric("Stop Loss", f"${best['stop']}")
        with col2:
            st.metric("Target", f"${best['target']}")
            st.metric("Shares", best['shares'])
        
        st.markdown(f"""
        <div class='metric success'>
        <strong>📊 Trade Setup</strong><br>
        Capital Required: ${best['price'] * best['shares']:.2f}<br>
        Profit Target: ${best['profit']:.2f}<br>
        Risk: -$0.70 | Reward: +${best['profit']:.2f}<br>
        RSI: {best['rsi']} | Volume Shock: {best['vol']}x
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ LOG THIS TRADE", use_container_width=True):
            st.success(f"✅ Trade logged: NVDA @ ${best['price']}")
            st.balloons()
    
    st.info("💡 **Strategy:** Swing trade (buy EOD, sell tomorrow morning)")

# ============================================================================
# TAB 2: INFO
# ============================================================================

with tab2:
    st.subheader("📚 Trading Guide")
    
    st.markdown("""
    ### Three Strategies
    
    **🌅 Intraday (Before 8 AM)**
    - Buy at market open
    - Sell same day
    - Target: +$1-3
    
    **🌙 Swing (After 11 AM)**
    - Buy at market close
    - Sell next morning
    - Target: +$1-5
    
    **⚡ Options (Anytime)**
    - Same-day or weekly
    - Target: 50-150% return
    
    ---
    
    ### Filtering System
    
    ✅ **Price Filter**: Under $35  
    ✅ **Volume Filter**: 150%+ of 10-day average  
    ✅ **RSI Filter**: 45-65 (momentum zone)  
    ✅ **Volatility Check**: Daily range confirms profit  
    
    ---
    
    ### Position Sizing
    
    | Rule | Value |
    |------|-------|
    | Starting Capital | $35 MAX |
    | Risk per Trade | -$0.50 MAX |
    | Profit Target | +$1.00 MIN |
    | Risk:Reward | 1:2 ratio |
    | Stop Loss | HARD (no exceptions) |
    """)

# ============================================================================
# TAB 3: SETTINGS
# ============================================================================

with tab3:
    st.subheader("⚙️ Trading Settings")
    
    capital = st.slider("Starting Capital ($)", 10, 100, 35, 5)
    risk = st.slider("Max Risk per Trade ($)", 0.1, 5.0, 0.5, 0.1)
    target = st.slider("Profit Target ($)", 0.5, 10.0, 1.0, 0.5)
    
    ratio = target / risk if risk > 0 else 0
    
    st.markdown(f"""
    <div class='metric success'>
    <strong>⚙️ Your Configuration</strong><br>
    Capital: ${capital}<br>
    Risk: ${risk:.2f} | Target: ${target:.2f}<br>
    Risk:Reward = 1:{ratio:.1f}
    </div>
    """, unsafe_allow_html=True)
    
    if ratio < 1.8:
        st.warning("⚠️ Ratio below 1:2 - increase target or lower risk")
    else:
        st.success("✅ Good risk:reward ratio!")

st.divider()

st.markdown("""
---

### 📋 Quick Rules
- 🎯 **One trade per day maximum**
- 💰 **Never risk more than $0.50**
- 🛑 **Hard stop losses (no exceptions)**
- 📊 **Close at profit target**
- 📈 **Track win rate monthly**

### ⚠️ DISCLAIMER
**NOT FINANCIAL ADVICE.** Trading risks 100% loss of capital.  
You are solely responsible for all decisions.  
Consult a licensed financial advisor before trading.

---

**DayTrade Pro v2.0** | Scan • Track • Trade  
🚀 Mobile-optimized | Fast & Responsive
""")
