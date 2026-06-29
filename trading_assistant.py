import streamlit as st
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try importing data libraries
try:
    import yfinance as yf
    import pandas as pd
    SCANNER_AVAILABLE = True
except:
    SCANNER_AVAILABLE = False

st.set_page_config(
    page_title="DayTrade Pro",
    page_icon="📈",
    layout="centered"
)

st.markdown("""
<style>
    h1, h2 { text-align: center; }
    .metric { background: #f0f2f6; padding: 12px; border-radius: 8px; margin: 8px 0; }
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
    st.error("Trading carries 100% loss risk. This is educational only. Consult an advisor.")

tab1, tab2, tab3 = st.tabs(["🔍 Scanner", "📊 Info", "⚙️ Settings"])

# ============================================================================
# TAB 1: SCANNER
# ============================================================================

with tab1:
    st.subheader("Market Scanner")
    
    if not SCANNER_AVAILABLE:
        st.warning("⏳ Scanner loading libraries... Please refresh if stuck.")
    else:
        @st.cache_data(ttl=300)
        def get_watchlist():
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX',
                    'MSTR', 'COIN', 'RIOT', 'HOOD', 'SOFI', 'UPST', 'PLTR', 'SMCI']
        
        def calculate_rsi(data, period=14):
            try:
                if len(data) < period:
                    return None
                delta = data['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(period).mean()
                loss = -delta.where(delta < 0, 0).rolling(period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            except:
                return None
        
        def scan_stock(ticker):
            try:
                hist = yf.download(ticker, period='30d', progress=False, timeout=5)
                if hist is None or len(hist) < 10:
                    return None
                
                price = float(hist['Close'].iloc[-1])
                if price > 35:
                    return None
                
                vol = float(hist['Volume'].iloc[-1])
                avg_vol = float(hist['Volume'].iloc[-11:-1].mean())
                vol_ratio = vol / avg_vol if avg_vol > 0 else 0
                
                if vol_ratio < 1.5:
                    return None
                
                rsi = calculate_rsi(hist)
                if rsi is None or rsi < 45 or rsi > 65:
                    return None
                
                shares = int((35 * 0.95) / price)
                if shares < 1:
                    return None
                
                daily_range = hist['High'].iloc[-1] - hist['Low'].iloc[-1]
                stop_loss = price - (daily_range * 0.5)
                target = price + (daily_range * 1.0)
                
                return {
                    'ticker': ticker,
                    'price': round(price, 2),
                    'shares': shares,
                    'stop': round(max(stop_loss, 0.01), 2),
                    'target': round(target, 2),
                    'profit': round(shares * (target - price), 2),
                    'rsi': round(rsi, 2),
                    'vol': round(vol_ratio, 1)
                }
            except:
                return None
        
        if st.button("🔍 SCAN MARKET", use_container_width=True, key="scan"):
            progress = st.progress(0)
            watchlist = get_watchlist()
            candidates = []
            
            for i, ticker in enumerate(watchlist):
                result = scan_stock(ticker)
                if result:
                    candidates.append(result)
                progress.progress((i + 1) / len(watchlist))
            
            if not candidates:
                st.warning("❌ No setups found today")
            else:
                candidates.sort(key=lambda x: (x['vol'], x['rsi']), reverse=True)
                best = candidates[0]
                
                st.success(f"✅ **{best['ticker']}** - BUY SETUP")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Entry", f"${best['price']}")
                    st.metric("Stop", f"${best['stop']}")
                with col2:
                    st.metric("Target", f"${best['target']}")
                    st.metric("Shares", best['shares'])
                
                st.markdown(f"""
                <div class='metric'>
                <strong>📊 Trade Details</strong><br>
                Capital: ${best['price'] * best['shares']:.2f}<br>
                Profit: ${best['profit']:.2f}<br>
                RSI: {best['rsi']} | Vol: {best['vol']}x
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("✅ LOG TRADE", use_container_width=True):
                    st.success(f"Logged: {best['ticker']} @ ${best['price']}")
                    st.balloons()

# ============================================================================
# TAB 2: INFO
# ============================================================================

with tab2:
    st.subheader("📚 Trading Guide")
    
    st.markdown("""
    ### Strategies
    
    **Intraday (Before 8 AM)**
    - Buy open, sell same day
    - Target: +$1-3
    
    **Swing (After 11 AM)**
    - Buy close, sell next morning
    - Target: +$1-5
    
    ### Filters
    
    ✅ Price < $35  
    ✅ Volume +150%  
    ✅ RSI 45-65  
    ✅ Profit achievable  
    
    ### Rules
    
    | Item | Value |
    |------|-------|
    | Max Capital | $35 |
    | Max Risk | -$0.50 |
    | Min Target | +$1.00 |
    | Risk:Reward | 1:2 |
    """)

# ============================================================================
# TAB 3: SETTINGS
# ============================================================================

with tab3:
    st.subheader("⚙️ Settings")
    
    capital = st.slider("Starting Capital ($)", 10, 100, 35, 5)
    risk = st.slider("Max Risk per Trade ($)", 0.1, 5.0, 0.5, 0.1)
    target = st.slider("Profit Target ($)", 0.5, 10.0, 1.0, 0.5)
    
    st.info(f"""
    **Active Configuration:**
    - Capital: ${capital}
    - Risk: ${risk:.2f}
    - Target: ${target:.2f}
    - Ratio: 1:{target/risk:.1f}
    """)

st.divider()
st.markdown("""
⚠️ **DISCLAIMER:** Not financial advice. Trading risks 100% loss.  
📈 **DayTrade Pro** | Scan • Track • Trade
""")
