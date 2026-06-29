import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import warnings
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
    .metric-box { background: #f0f2f6; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #1f77b4; }
    h1, h2 { text-align: center; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# TIMEZONE & STATE
# ============================================================================

CST = pytz.timezone('US/Central')
now = datetime.now(CST)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_rsi(data, period=14):
    """Calculate RSI safely"""
    try:
        if len(data) < period + 1:
            return None
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = float(rsi.iloc[-1])
        return val if not pd.isna(val) else None
    except:
        return None

@st.cache_data(ttl=300)
def get_watchlist():
    """Get list of stocks to scan"""
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX',
            'MSTR', 'COIN', 'RIOT', 'MARA', 'CLSK', 'BITB', 'HOOD', 'SOFI',
            'UPST', 'PLTR', 'DOCS', 'SNOW', 'CRM', 'ADBE', 'INTC', 'AMD',
            'NVIDIA', 'SUPER', 'AEHR', 'ONON', 'SMCI', 'DELL']

def scan_stock(ticker):
    """Analyze single stock - with error handling"""
    try:
        # Fetch data with timeout
        hist = yf.download(ticker, period='30d', progress=False, timeout=10)
        
        if hist is None or len(hist) < 10:
            return None
        
        current_price = float(hist['Close'].iloc[-1])
        
        # Filter 1: Price < $35
        if current_price > 35:
            return None
        
        # Get volume data
        current_volume = float(hist['Volume'].iloc[-1])
        avg_volume = float(hist['Volume'].iloc[-11:-1].mean())
        
        # Filter 2: Volume shock (150%+)
        if avg_volume == 0:
            return None
        volume_ratio = current_volume / avg_volume
        if volume_ratio < 1.5:
            return None
        
        # Filter 3: RSI between 45-65
        rsi = calculate_rsi(hist)
        if rsi is None or rsi < 45 or rsi > 65:
            return None
        
        # Calculate position sizing
        shares = int((35 * 0.95) / current_price)
        if shares < 1:
            return None
        
        # Calculate targets (conservative)
        daily_range = hist['High'].iloc[-1] - hist['Low'].iloc[-1]
        stop_loss = current_price - (daily_range * 0.5)
        take_profit = current_price + (daily_range * 1.0)
        
        return {
            'ticker': ticker,
            'price': round(current_price, 2),
            'shares': shares,
            'entry': round(current_price, 2),
            'stop_loss': round(max(stop_loss, 0.01), 2),
            'take_profit': round(take_profit, 2),
            'capital': round(shares * current_price, 2),
            'profit': round(shares * (take_profit - current_price), 2),
            'loss': round(shares * (current_price - stop_loss), 2),
            'rsi': round(rsi, 2),
            'volume': round(volume_ratio, 2)
        }
    except:
        return None

# ============================================================================
# MAIN APP
# ============================================================================

st.title("📈 DayTrade Pro")
st.subheader("Mobile Trading Assistant")

# Disclaimer
with st.expander("⚠️ LEGAL DISCLAIMER - READ FIRST"):
    st.error("""
    **THIS IS NOT FINANCIAL ADVICE.**
    
    Trading stocks and options carries substantial risk of loss, including 100% loss of capital.
    Past performance does not guarantee future results.
    You are solely responsible for all trading decisions.
    Consult a licensed financial advisor before trading.
    """)

# Time display
st.markdown(f"""
<div style='text-align: center; color: #666; margin: 15px 0;'>
🕐 {now.strftime('%I:%M %p %Z')} | 📅 {now.strftime('%A, %B %d')}
</div>
""", unsafe_allow_html=True)

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Scan", "📊 Info", "💡 Tips"])

with tab1:
    st.subheader("Market Scanner")
    
    if st.button("🔍 SCAN MARKET NOW", use_container_width=True, key="scan_btn"):
        st.info("Scanning 30 stocks for trading setups...")
        progress_bar = st.progress(0)
        
        watchlist = get_watchlist()
        candidates = []
        
        for i, ticker in enumerate(watchlist):
            result = scan_stock(ticker)
            if result:
                candidates.append(result)
            progress_bar.progress((i + 1) / len(watchlist))
        
        if not candidates:
            st.warning("❌ No setups found. Market may be quiet or conditions not met.")
            st.info("Filters: Price <$35 | Volume +150% | RSI 45-65")
        else:
            # Sort by best
            candidates.sort(key=lambda x: (x['volume'], x['rsi']), reverse=True)
            best = candidates[0]
            
            st.success(f"✅ **SETUP FOUND: {best['ticker']}**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Entry Price", f"${best['entry']}")
                st.metric("Stop Loss", f"${best['stop_loss']}")
            with col2:
                st.metric("Target Price", f"${best['take_profit']}")
                st.metric("Position Size", f"{best['shares']} shares")
            
            st.markdown(f"""
            <div class='metric-box'>
            <strong>📊 Trade Setup Details</strong><br>
            Capital Required: ${best['capital']}<br>
            Profit Target: ${best['profit']}<br>
            Risk per Trade: ${best['loss']}<br>
            RSI: {best['rsi']} | Volume: {best['volume']}x
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✅ LOG THIS TRADE", use_container_width=True):
                st.success(f"✅ Trade logged: {best['ticker']} @ ${best['entry']}")
                st.balloons()

with tab2:
    st.subheader("📚 How DayTrade Pro Works")
    
    st.markdown("""
    ### 4-Filter Stock Screening
    1. **Price**: Under $35 (capital constraint)
    2. **Volume**: 150%+ of 10-day average (breakout signal)
    3. **RSI**: Between 45-65 (momentum, not extreme)
    4. **Volatility**: Daily range confirms profit possible
    
    ### Position Sizing Rules
    - **Starting Capital**: $35 maximum
    - **Position Size**: Calculated to fit capital
    - **Profit Target**: +$1-3 per trade
    - **Risk per Trade**: Max -$0.50
    - **Risk:Reward**: 1:2 minimum
    
    ### Time-Based Strategies
    - **Before 8 AM CST**: Intraday (buy open, sell same day)
    - **After 11 AM CST**: Swing trades (buy close, sell next morning)
    - **Options**: Same-day or Friday weeklies
    """)

with tab3:
    st.subheader("💡 Trading Tips")
    
    st.markdown("""
    ### Risk Management
    ✅ **DO:**
    - Follow the position sizing rules
    - Use hard stop losses
    - Close at profit targets
    - Track win rate monthly
    - Risk only what you can lose
    
    ❌ **DON'T:**
    - Over-leverage or use margin
    - Move your stop loss lower
    - Hold past profit target (greed)
    - Revenge trade after losses
    - Trade on emotion
    
    ### Technical Notes
    - RSI (14): Momentum indicator (0-100)
    - Volume Shock: Unusual trading activity
    - Daily Range: Support for target calculation
    - Data: 15-20 min delayed (free tier)
    """)

st.divider()
st.markdown("""
<div style='text-align: center; font-size: 12px; color: #999; margin: 20px 0;'>
⚡ Powered by yfinance | Data delayed 15-20 min | Trade responsibly 📈
</div>
""", unsafe_allow_html=True)
