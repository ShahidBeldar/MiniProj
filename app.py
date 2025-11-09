import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from analyzer import analyze_headline
from utils import get_stock_data
from login import login_page
import time


# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="Finance News Impact Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
if "analysis_history" not in st.session_state:
    st.session_state["analysis_history"] = []
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

def show_analysis_progress():
    statuses = [
        "Analyzing headline sentiment...",
        "Fetching market data...",
        "Computing AI predictions...",
        "Calculating impact scores...",
        "Finalizing results..."
    ]
    for status in statuses:
        with st.spinner(status):
            time.sleep(0.6)

# --- THEME TOGGLE FUNCTION ---
def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"

# --- DYNAMIC CSS BASED ON THEME ---
def get_theme_css():
    if st.session_state["theme"] == "dark":
        return """
        <style>
            .main-header {
                font-size: 2.8rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
                margin-bottom: 0;
                letter-spacing: -1px;
            }
            .sub-text {
                font-size: 1.15rem;
                color: #9CA3AF;
                margin-bottom: 2rem;
                font-weight: 400;
            }
            [data-testid="stMetricValue"] {
                font-size: 2rem;
                font-weight: 700;
            }
            .stApp {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            .metric-card {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #334155;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            .info-box {
                background: #1e293b;
                padding: 1.2rem;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                margin: 1rem 0;
            }
            .positive-impact { color: #10b981; font-weight: 600; }
            .negative-impact { color: #ef4444; font-weight: 600; }
            .neutral-impact { color: #f59e0b; font-weight: 600; }
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 12px 24px;
                border: 1px solid #334155;
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
            }
            .section-header {
                font-size: 1.5rem;
                font-weight: 600;
                color: #e2e8f0;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
            }
        </style>
        """
    else:
        return """
        <style>
            .main-header {
                font-size: 2.8rem;
                background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
                margin-bottom: 0;
                letter-spacing: -1px;
            }
            .sub-text {
                font-size: 1.15rem;
                color: #4B5563;
                margin-bottom: 2rem;
                font-weight: 400;
            }
            [data-testid="stMetricValue"] {
                font-size: 2rem;
                font-weight: 700;
            }
            .metric-card {
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            .info-box {
                background: #f0f9ff;
                padding: 1.2rem;
                border-radius: 10px;
                border-left: 4px solid #2563eb;
                margin: 1rem 0;
            }
            .positive-impact { color: #059669; font-weight: 600; }
            .negative-impact { color: #dc2626; font-weight: 600; }
            .neutral-impact { color: #d97706; font-weight: 600; }
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: #f8fafc;
                border-radius: 8px;
                padding: 12px 24px;
                border: 1px solid #e2e8f0;
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                color: white;
                border: none;
            }
            .section-header {
                font-size: 1.5rem;
                font-weight: 600;
                color: #1e293b;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
            }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

# --- LOGIN CHECK ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_page()
    st.stop()

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### Settings")
    
    # Theme Toggle
    theme_label = "Switch to Dark Mode" if st.session_state["theme"] == "light" else "Switch to Light Mode"
    if st.button(theme_label, use_container_width=True):
        toggle_theme()
        st.rerun()
    
    st.divider()
    
    # Quick Access to Favorites
    st.markdown("### Favorite Tickers")
    if st.session_state["favorites"]:
        for fav in st.session_state["favorites"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(fav, use_container_width=True, key=f"fav_{fav}"):
                    st.session_state["selected_ticker"] = fav
            with col2:
                if st.button("×", key=f"remove_{fav}"):
                    st.session_state["favorites"].remove(fav)
                    st.rerun()
    else:
        st.info("No favorites yet. Add tickers from the main form.")
    
    st.divider()
    
    # Analysis History
    st.markdown("### Recent Analyses")
    if st.session_state["analysis_history"]:
        for i, hist in enumerate(st.session_state["analysis_history"][-5:]):
            with st.expander(f"{hist['ticker']} - {hist['timestamp'][:10]}"):
                st.write(f"**Headline:** {hist['headline'][:60]}...")
                st.write(f"**Impact:** {hist['impact']}")
                st.write(f"**Polarity:** {hist['polarity']:.2f}")
    else:
        st.info("No analysis history yet.")
    
    st.divider()
    
    # Export Options
    st.markdown("### Export Data")
    if st.button("Download History as CSV", use_container_width=True):
        if st.session_state["analysis_history"]:
            df_history = pd.DataFrame(st.session_state["analysis_history"])
            csv = df_history.to_csv(index=False)
            st.download_button(
                label="Download CSV File",
                data=csv,
                file_name=f"analysis_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("No history to export")
    
    st.divider()
    
    # About Section
    with st.expander("About This Application"):
        st.markdown("""
        **Version:** 2.0  
        **Features:**
        - AI-powered sentiment analysis
        - Real-time stock data
        - Historical comparisons
        - Dark/Light mode
        - Analysis history tracking
        - Multi-metric visualization
        """)

# --- TOP NAVIGATION BAR ---
col_nav1, col_nav2 = st.columns([8, 1])
with col_nav1:
    st.markdown('<div class="main-header">Finance News Impact Simulator</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">AI-powered sentiment analysis for real-time market impact prediction</p>', unsafe_allow_html=True)

with col_nav2:
    st.write("")
    st.write("")
    if st.button("Logout", type="secondary", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

st.divider()

# --- CONFIGURATION SECTION ---
with st.container():
    st.markdown('<p class="section-header">Simulation Parameters</p>', unsafe_allow_html=True)
    config_col1, config_col2, config_col3 = st.columns([3, 3, 3])
    
    with config_col1:
        ticker_default = st.session_state.get("selected_ticker", "TSLA")
        ticker = st.text_input(
            "Stock Ticker Symbol", 
            value=ticker_default, 
            help="Enter standard ticker symbols (e.g., AAPL, MSFT, RELIANCE.NS)"
        ).upper()
        
    with config_col2:
        period = st.selectbox(
            "Historical Data Period", 
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], 
            index=3,
            help="Select how far back to pull stock data for context."
        )
    
    with config_col3:
        comparison_ticker = st.text_input(
            "Compare With (Optional)",
            value="",
            placeholder="e.g., SPY",
            help="Add a benchmark ticker for comparison"
        ).upper()

# --- MAIN INPUT SECTION ---
st.markdown('<p class="section-header">News Analysis</p>', unsafe_allow_html=True)

headline_input = st.text_area(
    "Enter News Headline for Simulation", 
    height=120, 
    placeholder="e.g., Federal Reserve unexpectedly cuts interest rates by 50 basis points amid growing recession concerns...",
    help="Enter any financial news headline to analyze its potential market impact"
)

analyze_button = st.button("Run Analysis", type="primary", use_container_width=False)

# --- ANALYSIS & RESULTS ---
if analyze_button and headline_input.strip():
        show_analysis_progress()
        try:
            # 1. Run Analysis
            result = analyze_headline(headline_input)
            stock_df = get_stock_data(ticker, period)
            
            # Get comparison data if ticker provided
            comparison_df = None
            if comparison_ticker:
                comparison_df = get_stock_data(comparison_ticker, period)
            
            # Save to history
            history_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ticker": ticker,
                "headline": headline_input,
                "polarity": result['polarity'],
                "impact": result['impact']
            }
            st.session_state["analysis_history"].insert(0, history_entry)
            if len(st.session_state["analysis_history"]) > 50:
                st.session_state["analysis_history"] = st.session_state["analysis_history"][:50]
            
            # --- RESULTS TABS ---
            tab_impact, tab_technical, tab_comparison, tab_historical, tab_raw = st.tabs([
                "Market Impact", 
                "Technical Analysis", 
                "Comparison",
                "Historical Context", 
                "Raw Data"
            ])

            with tab_impact:
                # --- KPIs Row ---
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                polarity_val = result['polarity']
                impact_label = result['impact']
                
                # Determine impact class
                if polarity_val > 0:
                    impact_class = "positive-impact"
                    delta_color = "normal"
                elif polarity_val < 0:
                    impact_class = "negative-impact"
                    delta_color = "inverse"
                else:
                    impact_class = "neutral-impact"
                    delta_color = "off"

                with kpi1:
                    st.metric("Target Ticker", ticker)
                
                with kpi2:
                    st.metric(
                        "Sentiment Polarity", 
                        f"{polarity_val:.2f}",
                        delta=f"{abs(polarity_val):.2f}",
                        delta_color=delta_color
                    )
                
                with kpi3:
                    st.markdown(f"**Predicted Impact**")
                    st.markdown(f"<p class='{impact_class}' style='font-size: 2rem; margin: 0;'>{impact_label}</p>", unsafe_allow_html=True)
                
                with kpi4:
                    if stock_df is not None and len(stock_df) > 1:
                        price_change = ((stock_df['Close'].iloc[-1] - stock_df['Close'].iloc[0]) / stock_df['Close'].iloc[0]) * 100
                        st.metric(
                            f"{period} Change", 
                            f"${stock_df['Close'].iloc[-1]:.2f}",
                            delta=f"{price_change:.2f}%"
                        )
                
                st.divider()
                
                # --- TRADING INSIGHTS SECTION ---
                if stock_df is not None and len(stock_df) >= 20:
                    st.markdown("#### Trading Insights & Risk Assessment")
                    
                    # Calculate additional metrics
                    returns = stock_df['Close'].pct_change().dropna()
                    current_price = stock_df['Close'].iloc[-1]
                    
                    # Calculate support and resistance levels
                    high_52w = stock_df['High'].tail(252).max() if len(stock_df) >= 252 else stock_df['High'].max()
                    low_52w = stock_df['Low'].tail(252).min() if len(stock_df) >= 252 else stock_df['Low'].min()
                    
                    # Bollinger Bands
                    rolling_mean = stock_df['Close'].rolling(window=20).mean().iloc[-1]
                    rolling_std = stock_df['Close'].rolling(window=20).std().iloc[-1]
                    upper_band = rolling_mean + (2 * rolling_std)
                    lower_band = rolling_mean - (2 * rolling_std)
                    
                    # Risk metrics
                    daily_volatility = returns.std()
                    sharpe_ratio = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() != 0 else 0
                    max_drawdown = ((stock_df['Close'] / stock_df['Close'].cummax()) - 1).min() * 100
                    
                    # Momentum indicators
                    momentum_5d = ((current_price - stock_df['Close'].iloc[-6]) / stock_df['Close'].iloc[-6] * 100) if len(stock_df) >= 6 else 0
                    momentum_20d = ((current_price - stock_df['Close'].iloc[-21]) / stock_df['Close'].iloc[-21] * 100) if len(stock_df) >= 21 else 0
                    
                    insight_col1, insight_col2, insight_col3 = st.columns(3)
                    
                    with insight_col1:
                        st.markdown("**Price Levels**")
                        st.metric("52-Week High", f"${high_52w:.2f}")
                        st.metric("52-Week Low", f"${low_52w:.2f}")
                        st.metric("Upper Bollinger Band", f"${upper_band:.2f}")
                        st.metric("Lower Bollinger Band", f"${lower_band:.2f}")
                        
                        # Distance from bands
                        distance_upper = ((upper_band - current_price) / current_price) * 100
                        distance_lower = ((current_price - lower_band) / current_price) * 100
                        st.caption(f"Distance to Upper: {distance_upper:.1f}%")
                        st.caption(f"Distance to Lower: {distance_lower:.1f}%")
                    
                    with insight_col2:
                        st.markdown("**Risk Metrics**")
                        st.metric("Daily Volatility", f"{daily_volatility*100:.2f}%")
                        st.metric("Annualized Volatility", f"{daily_volatility*100*(252**0.5):.2f}%")
                        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                        st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
                        
                        # Risk interpretation
                        if daily_volatility < 0.015:
                            risk_level = "Low Risk"
                        elif daily_volatility < 0.025:
                            risk_level = "Moderate Risk"
                        else:
                            risk_level = "High Risk"
                        st.caption(f"Risk Level: {risk_level}")
                    
                    with insight_col3:
                        st.markdown("**Momentum Indicators**")
                        st.metric("5-Day Momentum", f"{momentum_5d:.2f}%", delta=f"{momentum_5d:.2f}%")
                        st.metric("20-Day Momentum", f"{momentum_20d:.2f}%", delta=f"{momentum_20d:.2f}%")
                        
                        # Trend analysis
                        ma_20 = stock_df['Close'].rolling(window=20).mean().iloc[-1]
                        ma_50 = stock_df['Close'].rolling(window=50).mean().iloc[-1] if len(stock_df) >= 50 else ma_20
                        
                        if current_price > ma_20 and ma_20 > ma_50:
                            trend = "Strong Uptrend"
                        elif current_price > ma_20:
                            trend = "Uptrend"
                        elif current_price < ma_20 and ma_20 < ma_50:
                            trend = "Strong Downtrend"
                        else:
                            trend = "Downtrend"
                        
                        st.metric("Current Trend", trend)
                        st.metric("20-Day MA", f"${ma_20:.2f}")
                        st.metric("50-Day MA", f"${ma_50:.2f}")
                    
                    st.divider()
                    
                    # Trading Recommendation based on sentiment + technicals
                    st.markdown("#### AI-Powered Trading Recommendation")
                    
                    recommendation_score = 0
                    reasons = []
                    
                    # Sentiment factor
                    if polarity_val > 0.3:
                        recommendation_score += 2
                        reasons.append("Strong positive sentiment detected")
                    elif polarity_val > 0:
                        recommendation_score += 1
                        reasons.append("Positive sentiment detected")
                    elif polarity_val < -0.3:
                        recommendation_score -= 2
                        reasons.append("Strong negative sentiment detected")
                    elif polarity_val < 0:
                        recommendation_score -= 1
                        reasons.append("Negative sentiment detected")
                    
                    # Technical factors
                    if momentum_20d > 5:
                        recommendation_score += 1
                        reasons.append("Strong positive momentum")
                    elif momentum_20d < -5:
                        recommendation_score -= 1
                        reasons.append("Negative momentum")
                    
                    if current_price > upper_band:
                        recommendation_score -= 1
                        reasons.append("Price above upper Bollinger Band (overbought)")
                    elif current_price < lower_band:
                        recommendation_score += 1
                        reasons.append("Price below lower Bollinger Band (oversold)")
                    
                    if sharpe_ratio > 1.0:
                        recommendation_score += 1
                        reasons.append("Favorable risk-adjusted returns")
                    
                    # Final recommendation
                    rec_col1, rec_col2 = st.columns([1, 2])
                    
                    with rec_col1:
                        if recommendation_score >= 3:
                            recommendation = "STRONG BUY"
                            rec_color = "#10b981"
                        elif recommendation_score >= 1:
                            recommendation = "BUY"
                            rec_color = "#34d399"
                        elif recommendation_score <= -3:
                            recommendation = "STRONG SELL"
                            rec_color = "#ef4444"
                        elif recommendation_score <= -1:
                            recommendation = "SELL"
                            rec_color = "#f87171"
                        else:
                            recommendation = "HOLD"
                            rec_color = "#f59e0b"
                        
                        st.markdown(f"<h2 style='color: {rec_color}; text-align: center;'>{recommendation}</h2>", unsafe_allow_html=True)
                        st.caption(f"Confidence Score: {abs(recommendation_score)}/5")
                    
                    with rec_col2:
                        st.markdown("**Key Factors:**")
                        for reason in reasons:
                            st.markdown(f"• {reason}")
                        
                        st.markdown("**Disclaimer:** This recommendation is based on AI analysis and should not be considered financial advice. Always conduct your own research and consult with a financial advisor before making investment decisions.")

                st.divider()

                # --- Enhanced Stock Chart with Volume ---
                if stock_df is not None:
                    st.markdown("#### Price & Volume Trend")
                    
                    # Create subplots with secondary y-axis
                    fig = make_subplots(
                        rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_heights=[0.7, 0.3],
                        subplot_titles=('Price', 'Volume')
                    )
                    
                    # Price chart with candlestick
                    fig.add_trace(
                        go.Scatter(
                            x=stock_df['Date'], 
                            y=stock_df['Close'], 
                            mode='lines', 
                            fill='tozeroy', 
                            name='Close Price',
                            line=dict(color='#667eea', width=2),
                            fillcolor='rgba(102, 126, 234, 0.2)'
                        ),
                        row=1, col=1
                    )
                    
                    # Add moving averages if enough data
                    if len(stock_df) >= 20:
                        stock_df['MA20'] = stock_df['Close'].rolling(window=20).mean()
                        fig.add_trace(
                            go.Scatter(
                                x=stock_df['Date'], 
                                y=stock_df['MA20'], 
                                mode='lines', 
                                name='20-Day MA',
                                line=dict(color='#f59e0b', width=1, dash='dash')
                            ),
                            row=1, col=1
                        )
                    
                    # Volume chart
                    colors = ['#10b981' if stock_df['Close'].iloc[i] >= stock_df['Close'].iloc[i-1] else '#ef4444' 
                              for i in range(1, len(stock_df))]
                    colors.insert(0, '#6b7280')
                    
                    fig.add_trace(
                        go.Bar(
                            x=stock_df['Date'], 
                            y=stock_df['Volume'], 
                            name='Volume',
                            marker_color=colors,
                            showlegend=False
                        ),
                        row=2, col=1
                    )
                    
                    theme_template = "plotly_dark" if st.session_state["theme"] == "dark" else "plotly_white"
                    fig.update_layout(
                        template=theme_template,
                        height=600,
                        hovermode="x unified",
                        margin=dict(l=0, r=0, t=40, b=0),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    fig.update_xaxes(title_text="Date", row=2, col=1)
                    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
                    fig.update_yaxes(title_text="Volume", row=2, col=1)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Key Statistics
                    st.markdown("#### Key Statistics")
                    stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
                    
                    with stat_col1:
                        st.metric("Current Price", f"${stock_df['Close'].iloc[-1]:.2f}")
                    with stat_col2:
                        st.metric("High", f"${stock_df['High'].max():.2f}")
                    with stat_col3:
                        st.metric("Low", f"${stock_df['Low'].min():.2f}")
                    with stat_col4:
                        avg_volume = stock_df['Volume'].mean()
                        st.metric("Avg Volume", f"{avg_volume/1e6:.2f}M")
                    with stat_col5:
                        volatility = stock_df['Close'].pct_change().std() * 100
                        st.metric("Volatility", f"{volatility:.2f}%")
                else:
                    st.error(f"Could not fetch stock data for ticker: {ticker}. Please verify the symbol.")

            with tab_technical:
                if stock_df is not None:
                    st.markdown("#### Technical Indicators")
                    
                    # Calculate technical indicators
                    stock_df['Returns'] = stock_df['Close'].pct_change()
                    stock_df['Cumulative_Returns'] = (1 + stock_df['Returns']).cumprod() - 1
                    
                    # RSI Calculation (14-period)
                    delta = stock_df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    stock_df['RSI'] = 100 - (100 / (1 + rs))
                    
                    tech_col1, tech_col2 = st.columns(2)
                    
                    with tech_col1:
                        # Returns Distribution
                        fig_returns = go.Figure()
                        fig_returns.add_trace(go.Histogram(
                            x=stock_df['Returns'].dropna() * 100,
                            nbinsx=50,
                            name='Daily Returns',
                            marker_color='#667eea'
                        ))
                        fig_returns.update_layout(
                            title="Daily Returns Distribution (%)",
                            template=theme_template,
                            height=400,
                            showlegend=False,
                            xaxis_title="Return (%)",
                            yaxis_title="Frequency"
                        )
                        st.plotly_chart(fig_returns, use_container_width=True)
                    
                    with tech_col2:
                        # RSI Chart
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(
                            x=stock_df['Date'],
                            y=stock_df['RSI'],
                            mode='lines',
                            name='RSI',
                            line=dict(color='#667eea', width=2)
                        ))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444", annotation_text="Overbought")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#10b981", annotation_text="Oversold")
                        fig_rsi.update_layout(
                            title="Relative Strength Index (RSI)",
                            template=theme_template,
                            height=400,
                            yaxis_title="RSI",
                            xaxis_title="Date"
                        )
                        st.plotly_chart(fig_rsi, use_container_width=True)
                    
                    # Cumulative Returns
                    fig_cum = go.Figure()
                    fig_cum.add_trace(go.Scatter(
                        x=stock_df['Date'],
                        y=stock_df['Cumulative_Returns'] * 100,
                        mode='lines',
                        fill='tozeroy',
                        name='Cumulative Returns',
                        line=dict(color='#667eea', width=2),
                        fillcolor='rgba(102, 126, 234, 0.2)'
                    ))
                    fig_cum.update_layout(
                        title=f"Cumulative Returns Over {period}",
                        template=theme_template,
                        height=400,
                        yaxis_title="Cumulative Return (%)",
                        xaxis_title="Date"
                    )
                    st.plotly_chart(fig_cum, use_container_width=True)

            with tab_comparison:
                if comparison_ticker and comparison_df is not None:
                    st.markdown(f"#### {ticker} vs {comparison_ticker}")
                    
                    # Normalize prices for comparison
                    stock_normalized = (stock_df['Close'] / stock_df['Close'].iloc[0]) * 100
                    comparison_normalized = (comparison_df['Close'] / comparison_df['Close'].iloc[0]) * 100
                    
                    fig_comp = go.Figure()
                    fig_comp.add_trace(go.Scatter(
                        x=stock_df['Date'],
                        y=stock_normalized,
                        mode='lines',
                        name=ticker,
                        line=dict(color='#667eea', width=2)
                    ))
                    fig_comp.add_trace(go.Scatter(
                        x=comparison_df['Date'],
                        y=comparison_normalized,
                        mode='lines',
                        name=comparison_ticker,
                        line=dict(color='#f59e0b', width=2)
                    ))
                    fig_comp.update_layout(
                        title="Normalized Price Comparison (Base = 100)",
                        template=theme_template,
                        height=500,
                        hovermode="x unified",
                        yaxis_title="Normalized Price",
                        xaxis_title="Date"
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
                    
                    # Performance Metrics
                    perf_col1, perf_col2, perf_col3 = st.columns(3)
                    
                    ticker_return = ((stock_df['Close'].iloc[-1] - stock_df['Close'].iloc[0]) / stock_df['Close'].iloc[0]) * 100
                    comp_return = ((comparison_df['Close'].iloc[-1] - comparison_df['Close'].iloc[0]) / comparison_df['Close'].iloc[0]) * 100
                    outperformance = ticker_return - comp_return
                    
                    with perf_col1:
                        st.metric(f"{ticker} Return", f"{ticker_return:.2f}%")
                    with perf_col2:
                        st.metric(f"{comparison_ticker} Return", f"{comp_return:.2f}%")
                    with perf_col3:
                        st.metric("Outperformance", f"{outperformance:.2f}%", delta=f"{outperformance:.2f}%")
                
                elif comparison_ticker:
                    st.warning(f"Could not fetch data for comparison ticker: {comparison_ticker}")
                else:
                    st.info("Enter a comparison ticker in the parameters above to see side-by-side analysis")

            with tab_historical:
                st.markdown("#### Similar Historical Headlines")
                st.markdown("""
                <div class='info-box'>
                <strong>Context:</strong> The AI model identified these real-world headlines with similar 
                semantic meaning and sentiment to help contextualize the potential market impact.
                </div>
                """, unsafe_allow_html=True)
                
                if 'matched' in result and len(result['matched']) > 0:
                    # Enhanced dataframe display
                    matched_df = pd.DataFrame(result['matched'])
                    st.dataframe(
                        matched_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "similarity": st.column_config.ProgressColumn(
                                "Similarity Score",
                                format="%.2f",
                                min_value=0,
                                max_value=1,
                            ),
                        }
                    )
                else:
                    st.info("No historical matches found in the database.")

            with tab_raw:
                st.markdown("#### Raw Analysis Data")
                
                col_json1, col_json2 = st.columns(2)
                
                with col_json1:
                    st.markdown("**Analysis Results:**")
                    st.json(result)
                
                with col_json2:
                    st.markdown("**Stock Data Summary:**")
                    if stock_df is not None:
                        summary_data = {
                            "ticker": ticker,
                            "period": period,
                            "data_points": len(stock_df),
                            "date_range": f"{stock_df['Date'].iloc[0]} to {stock_df['Date'].iloc[-1]}",
                            "price_range": f"${stock_df['Low'].min():.2f} - ${stock_df['High'].max():.2f}",
                            "latest_close": f"${stock_df['Close'].iloc[-1]:.2f}"
                        }
                        st.json(summary_data)
                
                # Download button for raw data
                if stock_df is not None:
                    csv = stock_df.to_csv(index=False)
                    st.download_button(
                        label="Download Stock Data (CSV)",
                        data=csv,
                        file_name=f"{ticker}_{period}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )

        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")
            with st.expander("Debug Information"):
                st.exception(e)

elif analyze_button and not headline_input.strip():
    st.warning("Please enter a headline to simulate.")

# --- FOOTER ---
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("Data provided by Yahoo Finance")
with footer_col2:
    st.caption("AI Analysis powered by advanced NLP models")
with footer_col3:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")