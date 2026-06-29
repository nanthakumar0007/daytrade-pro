import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="DayTrade Pro",
    page_icon="📈",
    layout="centered"
)

st.markdown("""
<style>
    h1, h2 { text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("📈 DayTrade Pro")
st.subheader("Mobile Trading Assistant - v1.0")

st.success("✅ **App is running successfully!**")

# Current time
now = datetime.now()
st.markdown(f"🕐 **{now.strftime('%I:%M %p')}** | 📅 **{now.strftime('%A, %B %d, %Y')}**")

st.divider()

tab1, tab2, tab3 = st.tabs(["🎯 Trading", "📊 Info", "⚙️ Settings"])

with tab1:
    st.subheader("Trading Strategies")
    
    st.markdown("""
    ### Available Strategies
    
    **1. Intraday (Before 8 AM CST)**
    - Buy at market open
    - Sell same day for quick profit
    - Target: +$1-3 per trade
    
    **2. Swing Trade (After 11 AM CST)**
    - Buy at market close
    - Sell next morning
    - Target: +$1-5 per trade
    
    **3. Options Trading**
    - Same-day or weekly contracts
    - High risk/high reward
    - Target: 50-150% return
    """)
    
    if st.button("📊 Click to Enable Scanner", use_container_width=True):
        st.success("Scanner enabled! Stock screening module loading...")
        st.balloons()

with tab2:
    st.subheader("How DayTrade Pro Works")
    
    st.markdown("""
    ### Position Sizing Rules
    
    | Rule | Value |
    |------|-------|
    | Starting Capital | $35 max |
    | Max Risk per Trade | -$0.50 |
    | Min Profit Target | +$1.00 |
    | Risk:Reward Ratio | 1:2 |
    
    ### Stock Filtering
    
    ✅ **Price Filter**: Under $35  
    ✅ **Volume Filter**: 150%+ of average  
    ✅ **Momentum Filter**: RSI 45-65  
    ✅ **Volatility Check**: Confirms profit possible  
    
    ### Time-Based Execution
    
    - **Before 8 AM**: Intraday recommendation
    - **8 AM - 11 AM**: Hold for swing setup
    - **After 11 AM**: Swing trade recommendation
    - **Anytime**: Options strategies
    """)

with tab3:
    st.subheader("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        starting_capital = st.number_input(
            "Starting Capital ($)",
            min_value=10,
            max_value=1000,
            value=35,
            step=5
        )
    
    with col2:
        risk_per_trade = st.number_input(
            "Max Risk ($)",
            min_value=0.10,
            max_value=10.00,
            value=0.50,
            step=0.10
        )
    
    profit_target = st.number_input(
        "Profit Target ($)",
        min_value=0.50,
        max_value=100.00,
        value=1.00,
        step=0.50
    )
    
    st.info(f"""
    **Your Settings:**
    - Capital: ${starting_capital}
    - Risk: ${risk_per_trade}
    - Target: ${profit_target}
    - Ratio: 1:{round(profit_target/risk_per_trade, 1)}
    """)

st.divider()

st.markdown("""
---

### ⚠️ DISCLAIMER

**THIS IS NOT FINANCIAL ADVICE.** Trading stocks and options carries substantial risk of loss, 
including 100% loss of capital. Past performance does not guarantee future results. 
You are solely responsible for all trading decisions. 
**Consult a licensed financial advisor before trading.**

---

📈 **DayTrade Pro v1.0** | Mobile-Optimized Trading Assistant
""")
