import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from analyzer import analyze_headline
from utils import get_stock_data
from login import login_page

# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="News Impact Simulator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A; /* Professional Dark Blue */
        font-weight: 700;
    }
    .sub-text {
        font-size: 1.1rem;
        color: #4B5563;
    }
    /* Highlight metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIN CHECK ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_page()
    st.stop()

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Simulation Parameters")
    st.markdown("Configure your market simulation settings below.")
    
    with st.form("config_form"):
        ticker = st.text_input(
            "Stock Ticker Symbol", 
            value="TSLA", 
            help="Enter standard ticker symbols (e.g., AAPL, MSFT, RELIANCE.NS)"
        ).upper()
        
        period = st.selectbox(
            "Historical Data Period", 
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], 
            index=3,
            help="Select how far back to pull stock data for context."
        )
        
        st.markdown("---")
        st.markdown("**Analysis Settings**")
        # You could add more advanced settings here later (e.g., AI model selection)
        
        apply_settings = st.form_submit_button("Update Chart Parameters")

    st.info("ℹ️ **Tip:** Ensure your ticker symbol matches Yahoo Finance standards.")

# --- MAIN PAGE HEADER ---
st.markdown('<div class="main-header">📈 Market Sentiment Simulator</div>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Analyze the potential market impact of breaking news headlines using AI-driven sentiment analysis.</p>', unsafe_allow_html=True)
st.divider()

# --- MAIN INPUT SECTION ---
col1, col2 = st.columns([3, 1])
with col1:
    headline_input = st.text_area(
        "📰 Enter News Headline for Simulation", 
        height=100, 
        placeholder="e.g., Federal Reserve unexpectedly cuts interest rates by 50 basis points..."
    )

with col2:
    st.write("") # Spacing
    st.write("") # Spacing
    analyze_button = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

# --- ANALYSIS & RESULTS ---
if analyze_button and headline_input.strip():
    with st.spinner("🔄 Running AI Sentiment Analysis & Fetching Market Data..."):
        # 1. Run Analysis
        try:
            result = analyze_headline(headline_input)
            stock_df = get_stock_data(ticker, period)
            
            st.success("Analysis Complete")

            # --- RESULTS TABS ---
            tab_impact, tab_historical, tab_raw = st.tabs(["📊 Market Impact", "🏛️ Historical Precedents", "📝 Raw Data"])

            with tab_impact:
                # --- KPIs Row ---
                kpi1, kpi2, kpi3 = st.columns(3)
                
                # Determine colors for metrics based on polarity
                polarity_val = result['polarity']
                impact_label = result['impact']
                
                # Example logic for color - adjust based on your actual data return format
                polarity_delta_color = "normal"
                if isinstance(polarity_val, (int, float)):
                     if polarity_val > 0.1: polarity_delta_color = "off" # Green-ish usually handled by Streamlit if we use delta
                     elif polarity_val < -0.1: polarity_delta_color = "inverse"

                with kpi1:
                    st.metric("Target Ticker", ticker)
                with kpi2:
                     st.metric("Sentiment Polarity", f"{polarity_val:.2f}")
                with kpi3:
                    st.metric("Predicted Impact", impact_label)

                # --- Enhanced Stock Chart ---
                if stock_df is not None:
                    st.subheader(f"Price Trend: {ticker}")
                    
                    # Create a more professional candlestick or area chart instead of a simple line
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
                    
                    # Add range slider for professional feel
                    fig.update_xaxes(rangeslider_visible=True)
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"⚠️ Could not fetch stock data for ticker: {ticker}. Please verify the symbol.")

            with tab_historical:
                st.subheader("Similar Historical Headlines")
                st.markdown("The AI found the following real-world headlines with similar semantic meaning:")
                # Use generic styling for dataframe to make it sortable/interactive
                st.dataframe(
                    result['matched'], 
                    use_container_width=True, 
                    hide_index=True
                )

            with tab_raw:
                st.markdown("**Raw Analysis Data**")
                st.json(result)

        except Exception as e:
            st.error(f"An error occurred during analysis: {e}")

elif analyze_button and not headline_input.strip():
    st.warning("⚠️ Please enter a headline to simulate.")
