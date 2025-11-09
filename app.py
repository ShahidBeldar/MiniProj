import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from analyzer import analyze_headline
from utils import get_stock_data
from login import login_page

# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="Finance News Impact Simulator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A; /* Professional Dark Blue */
        font-weight: 700;
        margin-bottom: 0;
    }
    .sub-text {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    /* Highlight metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #111827;
    }
    /* Adjust logout button alignment */
    div.stButton > button:first-child {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIN CHECK ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_page()
    st.stop()

# --- TOP NAVIGATION BAR ---
col_nav1, col_nav2 = st.columns([8, 1])
with col_nav1:
    st.markdown('<div class="main-header">Finance News Impact Simulator</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Analyze the potential market impact of breaking news headlines using AI-driven sentiment analysis.</p>', unsafe_allow_html=True)
with col_nav2:
    # Spacer to align button better with title
    st.write("")
    if st.button("Logout", type="secondary"):
        st.session_state["logged_in"] = False
        st.rerun()

st.divider()

# --- CONFIGURATION SECTION ---
with st.container():
    st.subheader("Simulation Parameters")
    config_col1, config_col2, config_col3 = st.columns([2, 2, 4])
    
    with config_col1:
        ticker = st.text_input(
            "Stock Ticker Symbol", 
            value="TSLA", 
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
        st.write("") # Empty column for spacing on wide screens

# --- MAIN INPUT SECTION ---
st.subheader("News Analysis")
input_col1, input_col2 = st.columns([5, 1])
with input_col1:
    headline_input = st.text_area(
        "Enter News Headline for Simulation", 
        height=100, 
        placeholder="e.g., Federal Reserve unexpectedly cuts interest rates by 50 basis points..."
    )

with input_col2:
    # Align the button with the text area
    st.write("")
    st.write("")
    analyze_button = st.button("Run Simulation", type="primary", use_container_width=True)

# --- ANALYSIS & RESULTS ---
if analyze_button and headline_input.strip():
    st.divider()
    with st.spinner("Running AI Sentiment Analysis & Fetching Market Data..."):
        try:
            # 1. Run Analysis
            result = analyze_headline(headline_input)
            stock_df = get_stock_data(ticker, period)
            
            # --- RESULTS TABS ---
            tab_impact, tab_historical, tab_raw = st.tabs(["Market Impact", "Historical Precedents", "Raw Data"])

            with tab_impact:
                # --- KPIs Row ---
                kpi1, kpi2, kpi3 = st.columns(3)
                
                polarity_val = result['polarity']
                impact_label = result['impact']

                with kpi1:
                    st.metric("Target Ticker", ticker)
                with kpi2:
                     st.metric("Sentiment Polarity", f"{polarity_val:.2f}")
                with kpi3:
                    st.metric("Predicted Impact", impact_label)

                # --- Enhanced Stock Chart ---
                if stock_df is not None:
                    st.subheader(f"Price Trend: {ticker}")
                    
                    fig = go.Figure()
                    
                    # Use Close price area chart for clean look
                    fig.add_trace(go.Scatter(
                        x=stock_df['Date'], 
                        y=stock_df['Close'], 
                        mode='lines', 
                        fill='tozeroy', 
                        name='Close Price',
                        line=dict(color='#1E3A8A', width=2)
                    ))
                    
                    fig.update_layout(
                        template="plotly_white", 
                        height=500,
                        hovermode="x unified",
                        margin=dict(l=0, r=0, t=30, b=0),
                        yaxis_title="Stock Price (USD)",
                        xaxis_title="Date",
                        showlegend=False
                    )
                    
                    fig.update_xaxes(rangeslider_visible=True)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Could not fetch stock data for ticker: {ticker}. Please verify the symbol.")

            with tab_historical:
                st.subheader("Similar Historical Headlines")
                st.write("The AI found the following real-world headlines with similar semantic meaning:")
                st.dataframe(
                    result['matched'], 
                    use_container_width=True, 
                    hide_index=True
                )

            with tab_raw:
                st.write("Raw Analysis Data")
                st.json(result)

        except Exception as e:
            st.error(f"An error occurred during analysis: {e}")

elif analyze_button and not headline_input.strip():
    st.warning("Please enter a headline to simulate.")
