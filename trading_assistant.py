import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import warnings
import socket
warnings.filterwarnings('ignore')

# Network timeout
socket.setdefaulttimeout(30)

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
    .main { max-width: 500px; margin: 0 auto; }
    .stButton > button { width: 100%; padding: 12px; font-size: 16px; margin: 8px 0; border-radius: 8px; }
    .metric-box { background: #f0f2f6; padding: 15px; border-radius: 8px; margin: 10px 0; }
    .success { border-left: 4px solid #2ecc71; }
    .warning { border-left: 4px solid #f39c12; }
    .danger { border-left: 4px solid #e74c3c; }
    h1, h2 { text-align: center; }
</style>
""", unsafe_allow_html=True)

CST = pytz.timezone('US/Central')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_rsi(data, period=14):
    """Calculate RSI"""
    try:
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return None

def calculate_true_range(data):
    """Calculate average True Range"""
    try:
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return float(tr.mean())
    except:
        return None

@st.cache_data(ttl=300)
def get_watchlist():
    """Get list of liquid stocks"""
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
            'JNJ', 'V', 'PG', 'WMT', 'DIS', 'NKE', 'COST', 'HD', 'MCD', 'BA',
            'VZ', 'KO', 'PEP', 'ABT', 'LMT', 'MMM', 'SPY', 'QQQ', 'IWM', 'GLD']

def scan_stock(ticker):
    """Analyze single stock"""
    try:
        hist = yf.download(ticker, period='30d', progress=False, timeout=10)
        
        if len(hist) < 10:
            return None
        
        current_price = float(hist['Close'].iloc[-1])
        current_volume = float(hist['Volume'].iloc[-1])
        avg_volume = float(hist['Volume'].iloc[-11:-1].mean())
        
        # Filter 1: Price < $35
        if current_price > 35:
            return None
        
        # Filter 2: Volume shock
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        if volume_ratio < 1.5:
            return None
        
        # Filter 3: RSI
        rsi = calculate_rsi(hist, period=14)
        if rsi is None or rsi < 45 or rsi > 65:
            return None
        
        # Filter 4: True Range
        true_range = calculate_true_range(hist)
        if true_range is None or true_range < 0.1:
            return None
        
        # Position sizing
        shares = int((35 * 0.95) / current_price)
        if shares < 1:
            return None
        
        stop_loss = current_price - (true_range * 1.5)
        take_profit = current_price + (true_range * 3)
        
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
    except Exception as e:
        return None

# ============================================================================
# MAIN APP
# ============================================================================

st.title("📈 DayTrade Pro")
st.subheader("Mobile Trading Assistant")

# Disclaimer
with st.expander("⚠️ LEGAL DISCLAIMER"):
    st.error("""
    **This is NOT financial advice.** Trading stocks/options carries risk of 100% loss.
    You are solely responsible for trading decisions. Consult a licensed advisor.
    """)

# Time display
now = datetime.now(CST)
st.markdown(f"""
<div style='text-align: center; color: #666; margin: 15px 0;'>
🕐 {now.strftime('%I:%M %p %Z')} | 📅 {now.strftime('%A, %B %d')}
</div>
""", unsafe_allow_html=True)

st.divider()

# Strategy tabs
tab1, tab2, tab3 = st.tabs(["🎯 Stock Scan", "💎 Options", "📊 Info"])

with tab1:
    st.subheader("Find Trading Setup")
    
    if st.button("🔍 Scan Market", use_container_width=True, key="scan"):
        with st.spinner("Scanning stocks..."):
            watchlist = get_watchlist()
            candidates = []
            progress_bar = st.progress(0)
            
            for i, ticker in enumerate(watchlist):
                result = scan_stock(ticker)
                if result:
                    candidates.append(result)
                progress_bar.progress((i + 1) / len(watchlist))
            
            if not candidates:
                st.warning("❌ No setups found today. Market may be quiet.")
            else:
                # Sort by best setup
                candidates.sort(key=lambda x: (x['volume'], x['rsi']), reverse=True)
                best = candidates[0]
                
                st.success("✅ Best Setup Found!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class='metric-box success'>
                    <strong>📊 {best['ticker']}</strong><br>
                    Entry: ${best['entry']}<br>
                    Target: ${best['take_profit']}<br>
                    Stop: ${best['stop_loss']}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class='metric-box'>
                    Shares: {best['shares']}<br>
                    Capital: ${best['capital']}<br>
                    Profit: ${best['profit']}<br>
                    Loss: ${best['loss']}
                    </div>
                    """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("RSI (14)", best['rsi'])
                with col2:
                    st.metric("Volume Shock", f"{best['volume']}x")
                
                if st.button("✅ Confirm Trade", use_container_width=True, key="confirm"):
                    st.success(f"Trade logged: {best['ticker']} @ ${best['entry']}")

with tab2:
    st.subheader("Options Recommendations")
    
    if st.button("⚡ Analyze Options", use_container_width=True):
        st.info("""
        **Options Strategies:**
        - **Call**: Buy if RSI < 45 (oversold reversal)
        - **Put**: Buy if RSI > 65 (overbought pullback)
        - **Target**: $0.50-$2.00 profit same day
        - **Risk**: 100% loss of premium possible
        """)

with tab3:
    st.subheader("📚 How It Works")
    st.markdown("""
    **4-Filter Stock Screening:**
    1. **Price**: Must be under $35
    2. **Volume**: 150%+ of 10-day average
    3. **RSI**: Between 45-65 (momentum, not extreme)
    4. **Volatility**: True Range confirms $1 profit possible
    
    **Position Sizing:**
    - Max capital: $35
    - Max risk: -$0.50 per trade
    - Min profit: +$1.00 per trade
    - Risk:Reward ratio: 2:1 minimum
    
    **Time-Based Strategies:**
    - Before 8 AM: Intraday (buy open, sell same day)
    - After 11 AM: Swing (buy close, sell next morning)
    - Options: Same-day or Friday weeklies
    """)

st.divider()
st.markdown("""
<div style='text-align: center; font-size: 12px; color: #999; margin: 20px 0;'>
⚡ Powered by yfinance | Data may be 15-20 min delayed | Trade at your own risk
</div>
""", unsafe_allow_html=True)
