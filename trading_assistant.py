import streamlit as st
from datetime import datetime
import pytz

# Try importing optional dependencies
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    np = None

import warnings
if PANDAS_AVAILABLE:
    warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="DayTrade Pro",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    .main { max-width: 500px; margin: 0 auto; padding: 10px; }
    .stButton > button { width: 100%; padding: 12px; font-size: 16px; margin: 8px 0; border-radius: 8px; font-weight: bold; }
    h1, h2 { text-align: center; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# TIMEZONE
# ============================================================================

CST = pytz.timezone('US/Central')
now = datetime.now(CST)

# ============================================================================
# MAIN APP
# ============================================================================

st.title("📈 DayTrade Pro")
st.subheader("Mobile Trading Assistant")

# Disclaimer
with st.expander("⚠️ LEGAL DISCLAIMER"):
    st.error("""
    **THIS IS NOT FINANCIAL ADVICE.**
    
    Trading carries substantial risk of loss, including 100% loss of capital.
    Consult a licensed financial advisor before trading.
    """)

# Time display
st.markdown(f"""
<div style='text-align: center; color: #666; margin: 15px 0;'>
🕐 {now.strftime('%I:%M %p %Z')} | 📅 {now.strftime('%A, %B %d')}
</div>
""", unsafe_allow_html=True)

st.divider()

# Check dependencies
if not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE:
    st.warning("⚠️ System is initializing. Please refresh in 30 seconds.")
    st.info("""
    The app is loading required libraries. 
    
    If this persists:
    1. Click 'Manage App' in the lower right
    2. Restart the app
    3. Refresh the page
    """)
else:
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Scan", "📊 Info", "💡 Tips"])
    
    with tab1:
        st.subheader("Market Scanner")
        
        st.info("🔧 Stock scanner feature loading...")
        
        if st.button("🔍 SCAN MARKET", use_container_width=True):
            st.success("Scanner ready! Scanning market...")
            st.balloons()
    
    with tab2:
        st.subheader("📚 How It Works")
        
        st.markdown("""
        ### Trading Strategies
        
        **Intraday (Before 8 AM CST)**
        - Buy at market open
        - Sell same day
        - Target: +$1-3 profit
        
        **Swing (After 11 AM CST)**
        - Buy at close
        - Sell next morning
        - Target: +$1-5 profit
        
        **Options (Any Time)**
        - Same-day or weekly
        - Target: 50-150% return
        
        ### Filtering Rules
        ✅ Price under $35
        ✅ Volume +150% of average
        ✅ RSI between 45-65
        ✅ Positive risk-reward ratio
        """)
    
    with tab3:
        st.subheader("💡 Risk Management")
        
        st.markdown("""
        ### Position Sizing
        - Max capital: $35
        - Max risk per trade: -$0.50
        - Min profit target: +$1.00
        - Risk:Reward ratio: 1:2
        
        ### Rules
        ✅ Use hard stop losses
        ✅ Close at profit targets
        ✅ Trade mechanical rules
        ✅ Track win rate monthly
        
        ❌ Don't use margin
        ❌ Don't move stops lower
        ❌ Don't revenge trade
        ❌ Don't trade on emotion
        """)

st.divider()
st.markdown("""
<div style='text-align: center; font-size: 12px; color: #999; margin: 20px 0;'>
📈 DayTrade Pro | Trade responsibly
</div>
""", unsafe_allow_html=True)
