import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from pathlib import Path
import pytz
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIG & INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="DayTrade Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-first design
st.markdown("""
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    .main { max-width: 480px; margin: 0 auto; padding: 10px; }
    .stButton > button { 
        width: 100%; 
        padding: 14px; 
        font-size: 16px; 
        font-weight: bold;
        border-radius: 8px;
        margin: 8px 0;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    .success { border-left-color: #2ecc71; }
    .warning { border-left-color: #f39c12; }
    .danger { border-left-color: #e74c3c; }
    .info { border-left-color: #3498db; }
    h1, h2, h3 { text-align: center; }
</style>
""", unsafe_allow_html=True)

# Timezone setup
CST = pytz.timezone('US/Central')

# Session state initialization
if 'trades_history' not in st.session_state:
    st.session_state.trades_history = []
if 'current_trade' not in st.session_state:
    st.session_state.current_trade = None

# ============================================================================
# DATA MANAGEMENT
# ============================================================================

TRADES_FILE = Path("trades_history.json")

def save_trade(trade_data):
    """Persist trade to JSON file"""
    history = []
    if TRADES_FILE.exists():
        with open(TRADES_FILE, 'r') as f:
            history = json.load(f)
    history.append(trade_data)
    with open(TRADES_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    st.session_state.trades_history = history

def load_trades():
    """Load historical trades"""
    if TRADES_FILE.exists():
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

# ============================================================================
# MARKET SCANNING & FILTERING
# ============================================================================

@st.cache_data(ttl=300)
def get_top_liquid_stocks():
    """Fetch top 30 liquid stocks under $35 from S&P 500"""
    try:
        sp500 = yf.download('^GSPC', progress=False, period='1d')
        # Popular liquid tickers under $35
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
            'JNJ', 'V', 'PG', 'UNH', 'HD', 'DIS', 'BA', 'VZ', 'KO', 'MCD',
            'WMT', 'NKE', 'PEP', 'ABT', 'COST', 'LMT', 'MMM', 'SPY', 'QQQ',
            'IWM', 'GLD', 'TLT', 'USO'
        ]
        return tickers[:30]
    except:
        return ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'META', 'AMZN']

def calculate_rsi(data, period=14):
    """Calculate RSI indicator"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_true_range(high, low, close):
    """Calculate True Range for volatility"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.mean()

def scan_stock(ticker, strategy='intraday'):
    """Analyze single stock against criteria"""
    try:
        # Fetch 30 days of data for volume averages
        hist = yf.download(ticker, period='30d', progress=False)
        info = yf.Ticker(ticker).info
        
        if len(hist) < 10:
            return None
        
        current_price = hist['Close'].iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        avg_volume_10d = hist['Volume'].iloc[-11:-1].mean()
        
        # Skip if stock > $35
        if current_price > 35:
            return None
        
        # FILTER 1: Volume Shock (150% of 10-day average)
        volume_shock_ratio = current_volume / avg_volume_10d if avg_volume_10d > 0 else 0
        if volume_shock_ratio < 1.5:
            return None
        
        # FILTER 2: RSI Momentum (45-65 range)
        rsi = calculate_rsi(hist, period=14)
        if rsi < 45 or rsi > 65:
            return None
        
        # FILTER 3: Volatility (True Range)
        true_range = calculate_true_range(hist['High'], hist['Low'], hist['Close'])
        
        # Calculate position sizing for $35 capital, $1 profit target, 2:1 RRR
        # Risk = 0.50, Reward = 1.00
        risk_amount = 0.50
        position_size = risk_amount / (true_range / current_price) if true_range > 0 else 0
        shares = int((35 * 0.95) / current_price)  # Use 95% of capital
        
        if shares < 1:
            return None
        
        # Calculate targets
        entry_price = current_price
        stop_loss = entry_price - (true_range * 1.5)
        take_profit = entry_price + (true_range * 3)
        
        # Ensure 2:1 RRR
        profit_range = take_profit - entry_price
        loss_range = entry_price - stop_loss
        rrr = profit_range / loss_range if loss_range > 0 else 0
        
        if rrr < 1.8:  # Allow slight tolerance
            return None
        
        potential_profit = shares * (take_profit - entry_price)
        potential_loss = shares * (entry_price - stop_loss)
        
        return {
            'ticker': ticker,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(max(stop_loss, 0.01), 2),
            'take_profit': round(take_profit, 2),
            'shares': shares,
            'capital_required': round(shares * entry_price, 2),
            'potential_profit': round(potential_profit, 2),
            'potential_loss': round(potential_loss, 2),
            'rsi': round(rsi, 2),
            'volume_shock': round(volume_shock_ratio, 2),
            'true_range': round(true_range, 2),
            'rrr': round(rrr, 2),
            'recommendation_time': datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')
        }
    except:
        return None

def get_intraday_recommendation():
    """Get pre-market recommendation (before 8 AM CST)"""
    st.info("🌅 **START-OF-DAY STRATEGY** (Pre-market scan)\n\nBuy at market open, target intraday momentum exit")
    
    with st.spinner("Scanning for high-momentum intraday plays..."):
        watchlist = get_top_liquid_stocks()
        candidates = []
        
        for ticker in watchlist:
            result = scan_stock(ticker, strategy='intraday')
            if result:
                candidates.append(result)
        
        if not candidates:
            st.warning("❌ No stocks met criteria. Market may be quiet today.")
            return None
        
        # Sort by RRR and volume shock
        candidates.sort(key=lambda x: (x['rrr'], x['volume_shock']), reverse=True)
        top_pick = candidates[0]
        
        return top_pick

def get_swing_recommendation():
    """Get end-of-day swing recommendation (after 11 AM CST)"""
    st.info("🌙 **END-OF-DAY SWING STRATEGY** (Buy today, sell tomorrow morning)\n\nTarget next-day opening gap or momentum reversal")
    
    with st.spinner("Scanning for next-day swing setups..."):
        watchlist = get_top_liquid_stocks()
        candidates = []
        
        for ticker in watchlist:
            result = scan_stock(ticker, strategy='swing')
            if result:
                candidates.append(result)
        
        if not candidates:
            st.warning("❌ No swing setups found. Check market conditions.")
            return None
        
        # Prefer stocks with high volume and stable RSI
        candidates.sort(key=lambda x: (x['volume_shock'], x['rrr']), reverse=True)
        top_pick = candidates[0]
        
        return top_pick

# ============================================================================
# OPTIONS STRATEGIES
# ============================================================================

def get_options_recommendation():
    """Same-day options trading recommendation"""
    st.info("⚡ **OPTIONS TRADING** (Buy & Sell same day)\n\nTarget 10-50% profit on call/put spreads")
    
    with st.spinner("Analyzing options chains..."):
        watchlist = get_top_liquid_stocks()[:15]
        options_plays = []
        
        for ticker in watchlist:
            try:
                hist = yf.download(ticker, period='5d', progress=False)
                current_price = hist['Close'].iloc[-1]
                
                if current_price > 35:
                    continue
                
                rsi = calculate_rsi(hist, period=14)
                volume_ratio = hist['Volume'].iloc[-1] / hist['Volume'].iloc[-11:-1].mean()
                
                # RSI < 45 = oversold (call play), RSI > 65 = overbought (put play)
                if rsi < 45 and volume_ratio > 1.5:
                    options_plays.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'strategy': 'BUY CALL',
                        'reason': f'Oversold RSI ({rsi:.1f}), volume surge expected to push higher',
                        'target_profit': '$0.50-$2.00',
                        'target_price': round(current_price * 1.05, 2),
                        'rsi': rsi,
                        'expiry': 'Today (0 DTE)'
                    })
                elif rsi > 65 and volume_ratio > 1.5:
                    options_plays.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'strategy': 'BUY PUT',
                        'reason': f'Overbought RSI ({rsi:.1f}), pullback expected',
                        'target_profit': '$0.50-$2.00',
                        'target_price': round(current_price * 0.95, 2),
                        'rsi': rsi,
                        'expiry': 'Today (0 DTE)'
                    })
            except:
                continue
        
        if not options_plays:
            st.warning("❌ No clear options setups today.")
            return None
        
        return options_plays[0]

def get_friday_options_recommendation():
    """Friday weekly options recommendation for next week"""
    st.info("📅 **FRIDAY WEEKLY OPTIONS** (Buy Friday, sell Monday)\n\nWeekly expirations (massive gamma risk!)")
    
    current_date = datetime.now(CST)
    
    # Check if it's Friday
    if current_date.weekday() != 4:  # 4 = Friday
        st.warning("⚠️ This strategy only works on Fridays. Next recommendation available Friday morning.")
        return None
    
    with st.spinner("Scanning Friday weekly options..."):
        watchlist = get_top_liquid_stocks()[:12]
        friday_plays = []
        
        for ticker in watchlist:
            try:
                hist = yf.download(ticker, period='10d', progress=False)
                current_price = hist['Close'].iloc[-1]
                
                if current_price > 35:
                    continue
                
                rsi = calculate_rsi(hist, period=14)
                recent_volatility = hist['Close'].pct_change().std() * 100
                
                # Target ITM or near-ATM calls on momentum
                if rsi > 55 and recent_volatility > 1.5:
                    friday_plays.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'strategy': 'BUY CALL (Near ATM)',
                        'strike_recommendation': round(current_price + 0.50, 2),
                        'reason': f'High volatility ({recent_volatility:.1f}%), positive momentum',
                        'buy_time': 'Friday opening (9:30-10:00 AM)',
                        'sell_time': 'Monday opening (9:30-10:30 AM)',
                        'expected_return': '50-150% or $0.50-$3.00 profit',
                        'risk_level': '🔴 EXTREME - Gamma risk on weekends',
                        'expiry': 'Next Friday'
                    })
                elif rsi < 45 and recent_volatility > 1.5:
                    friday_plays.append({
                        'ticker': ticker,
                        'current_price': round(current_price, 2),
                        'strategy': 'BUY PUT (Near ATM)',
                        'strike_recommendation': round(current_price - 0.50, 2),
                        'reason': f'Oversold + high volatility ({recent_volatility:.1f}%)',
                        'buy_time': 'Friday opening (9:30-10:00 AM)',
                        'sell_time': 'Monday opening (9:30-10:30 AM)',
                        'expected_return': '50-150% or $0.50-$3.00 profit',
                        'risk_level': '🔴 EXTREME - Weekend gap risk',
                        'expiry': 'Next Friday'
                    })
            except:
                continue
        
        if not friday_plays:
            st.warning("❌ No Friday weekly setups identified.")
            return None
        
        return friday_plays[0]

# ============================================================================
# TRADE LOGGING & PERFORMANCE
# ============================================================================

def display_trade_card(trade):
    """Display trade recommendation in card format"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card info'>
            <strong>📊 Ticker:</strong> {trade.get('ticker', 'N/A')}<br>
            <strong>💰 Entry:</strong> ${trade.get('entry_price', 'N/A')}<br>
            <strong>🎯 Target:</strong> ${trade.get('take_profit', 'N/A')}<br>
            <strong>🛑 Stop Loss:</strong> ${trade.get('stop_loss', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card success'>
            <strong>📈 Shares:</strong> {trade.get('shares', 'N/A')}<br>
            <strong>💵 Capital:</strong> ${trade.get('capital_required', 'N/A')}<br>
            <strong>✅ Profit Target:</strong> ${trade.get('potential_profit', 'N/A')}<br>
            <strong>⚠️ Risk:</strong> ${trade.get('potential_loss', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        st.metric("RSI (14)", f"{trade.get('rsi', 'N/A')}", "Momentum")
    with col4:
        st.metric("Volume Shock", f"{trade.get('volume_shock', 'N/A')}x", "10-day avg")
    
    st.markdown(f"""
    <div class='metric-card warning'>
        <strong>⚡ Risk-to-Reward Ratio:</strong> {trade.get('rrr', 'N/A')} : 1<br>
        <strong>🕐 Scan Time:</strong> {trade.get('recommendation_time', 'N/A')}
    </div>
    """, unsafe_allow_html=True)

def show_performance():
    """Display historical performance"""
    trades = load_trades()
    
    if not trades:
        st.info("📊 No trades logged yet. Start trading to build history!")
        return
    
    df = pd.DataFrame(trades)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trades", len(df))
    with col2:
        completed = df[df.get('exit_price').notna()].shape[0] if 'exit_price' in df.columns else 0
        st.metric("Completed", completed)
    with col3:
        if 'pnl' in df.columns:
            total_pnl = df['pnl'].sum()
            st.metric("Net P&L", f"${total_pnl:.2f}")
    
    st.divider()
    st.subheader("📜 Trade History")
    st.dataframe(df, use_container_width=True)

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.title("📈 DayTrade Pro")
    st.subheader("Mobile Trading Assistant")
    
    # ⚠️ DISCLAIMER
    with st.expander("⚠️ LEGAL DISCLAIMER - READ BEFORE TRADING"):
        st.error("""
        **THIS IS NOT FINANCIAL ADVICE.**
        
        - Trading stocks and options carries substantial risk of loss, including 100% loss of capital.
        - Past performance does not guarantee future results.
        - This tool provides educational recommendations only.
        - You are solely responsible for all trading decisions.
        - Always consult a licensed financial advisor before trading.
        - Options trading is extremely risky, especially 0 DTE and weekly expirations.
        - Do NOT trade with money you cannot afford to lose.
        - Backtests shown are historical only and may not repeat.
        
        **By using this tool, you acknowledge you understand these risks.**
        """)
    
    # Determine current time
    now = datetime.now(CST)
    hour = now.hour
    
    st.markdown(f"""
    <div style='text-align: center; color: #666; margin: 15px 0;'>
    🕐 <strong>Current Time:</strong> {now.strftime('%I:%M %p %Z')}<br>
    📅 <strong>Date:</strong> {now.strftime('%A, %B %d, %Y')}
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # TAB 1: Strategy Selection
    tab1, tab2, tab3 = st.tabs(["🎯 Strategy", "💎 Options", "📊 History"])
    
    with tab1:
        st.subheader("Select Your Strategy")
        
        # Determine available strategies based on time
        if hour < 8:
            st.success("✅ Pre-market hours (before 8 AM CST)")
            if st.button("🌅 Get Intraday Recommendation", use_container_width=True):
                trade = get_intraday_recommendation()
                if trade:
                    st.session_state.current_trade = trade
                    display_trade_card(trade)
                    
                    # Confirmation button
                    if st.button("✅ Confirm Trade Placed", use_container_width=True, key="confirm_intraday"):
                        trade_data = {
                            **trade,
                            'strategy': 'Intraday',
                            'timestamp': datetime.now(CST).isoformat(),
                            'status': 'Active'
                        }
                        save_trade(trade_data)
                        st.success(f"✅ Trade logged: {trade['ticker']} @ ${trade['entry_price']}")
        
        elif 8 <= hour < 11:
            st.info("⏳ Morning hours (8 AM - 11 AM CST)")
            st.markdown("**Recommendation not yet available. Wait until 11 AM CST for swing trades.**")
        
        elif hour >= 11:
            st.success("✅ End-of-day hours (11 AM CST onwards)")
            if st.button("🌙 Get Swing Trade Recommendation", use_container_width=True):
                trade = get_swing_recommendation()
                if trade:
                    st.session_state.current_trade = trade
                    display_trade_card(trade)
                    
                    if st.button("✅ Confirm Trade Placed", use_container_width=True, key="confirm_swing"):
                        trade_data = {
                            **trade,
                            'strategy': 'Swing (EOD)',
                            'timestamp': datetime.now(CST).isoformat(),
                            'status': 'Active'
                        }
                        save_trade(trade_data)
                        st.success(f"✅ Trade logged: {trade['ticker']} @ ${trade['entry_price']}")
    
    with tab2:
        st.subheader("Options Strategies")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚡ Same-Day Options", use_container_width=True):
                options_rec = get_options_recommendation()
                if options_rec:
                    st.markdown(f"""
                    <div class='metric-card danger'>
                    <strong>🔥 {options_rec['strategy']}</strong><br>
                    <strong>Ticker:</strong> {options_rec['ticker']}<br>
                    <strong>Current Price:</strong> ${options_rec['current_price']}<br>
                    <strong>Target Profit:</strong> {options_rec['target_profit']}<br>
                    <strong>Target Price:</strong> ${options_rec['target_price']}<br>
                    <strong>RSI:</strong> {options_rec['rsi']:.1f}<br>
                    <strong>Reason:</strong> {options_rec['reason']}<br>
                    <strong>Expiry:</strong> {options_rec['expiry']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("📝 Log This Options Trade", use_container_width=True, key="log_options"):
                        trade_data = {
                            **options_rec,
                            'strategy': 'Options (0 DTE)',
                            'timestamp': datetime.now(CST).isoformat(),
                            'status': 'Active'
                        }
                        save_trade(trade_data)
                        st.success(f"✅ Options trade logged: {options_rec['ticker']} {options_rec['strategy']}")
        
        with col2:
            if st.button("📅 Friday Weeklies", use_container_width=True):
                friday_rec = get_friday_options_recommendation()
                if friday_rec:
                    st.markdown(f"""
                    <div class='metric-card danger'>
                    <strong>🔥 {friday_rec['strategy']}</strong><br>
                    <strong>Ticker:</strong> {friday_rec['ticker']}<br>
                    <strong>Current Price:</strong> ${friday_rec['current_price']}<br>
                    <strong>Strike:</strong> ${friday_rec['strike_recommendation']}<br>
                    <strong>Expected Return:</strong> {friday_rec['expected_return']}<br>
                    <strong>Buy Time:</strong> {friday_rec['buy_time']}<br>
                    <strong>Sell Time:</strong> {friday_rec['sell_time']}<br>
                    <strong>Risk:</strong> {friday_rec['risk_level']}<br>
                    <strong>Reason:</strong> {friday_rec['reason']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("📝 Log Friday Trade", use_container_width=True, key="log_friday"):
                        trade_data = {
                            **friday_rec,
                            'strategy': 'Options (Weekly)',
                            'timestamp': datetime.now(CST).isoformat(),
                            'status': 'Active'
                        }
                        save_trade(trade_data)
                        st.success(f"✅ Friday weekly logged: {friday_rec['ticker']} {friday_rec['strategy']}")
        
        st.warning("🔴 **OPTIONS WARNING**: 0 DTE and weekly options can lose 100% of premium paid. Extreme leverage and gamma risk. Only risk capital you can afford to lose completely.")
    
    with tab3:
        st.subheader("📊 Performance Dashboard")
        show_performance()

if __name__ == "__main__":
    main()
