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


st.set_page_config(
    page_title="Finance News Impact Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
if "analysis_history" not in st.session_state:
    st.session_state["analysis_history"] = []
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_analysis" not in st.session_state:
    st.session_state["current_analysis"] = None
if "show_guide" not in st.session_state:
    st.session_state["show_guide"] = False

def show_analysis_progress():
    statuses = [
        "Analyzing headline sentiment...",
        "Checking relevance to ticker...",
        "Fetching real-time market data...",
        "Computing predictions...",
        "Finalizing results..."
    ]
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, status in enumerate(statuses):
        status_text.text(status)
        progress_bar.progress((i + 1) / len(statuses))
        time.sleep(0.8)
    
    progress_bar.empty()
    status_text.empty()

def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"

def get_theme_css():
    if st.session_state["theme"] == "dark":
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            * {
                font-family: 'Inter', sans-serif;
            }
            
            .stApp {
                background: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 100%);
                color: #e8eaed;
            }
            
            .hero-glass {
                background: rgba(59, 130, 246, 0.08);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 24px;
                padding: 2.5rem;
                margin-bottom: 2rem;
                box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
                animation: fadeInScale 0.6s ease-out;
            }
            
            @keyframes fadeInScale {
                from {
                    opacity: 0;
                    transform: scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }
            
            .main-header {
                font-size: 3rem;
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
                margin-bottom: 0.5rem;
                letter-spacing: -1.5px;
                line-height: 1.2;
            }
            
            .sub-text {
                font-size: 1.1rem;
                color: #94a3b8;
                margin-bottom: 0;
                font-weight: 400;
                line-height: 1.6;
            }
            
            .classification-glass {
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                animation: fadeInScale 0.8s ease-out;
                transition: all 0.3s ease;
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .classification-glass:hover {
                transform: translateY(-4px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            }
            
            .glass-strong-positive {
                background: rgba(16, 185, 129, 0.15);
                border: 2px solid rgba(16, 185, 129, 0.4);
                box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
            }
            
            .glass-positive {
                background: rgba(52, 211, 153, 0.12);
                border: 2px solid rgba(52, 211, 153, 0.3);
                box-shadow: 0 8px 32px rgba(52, 211, 153, 0.2);
            }
            
            .glass-neutral {
                background: rgba(100, 116, 139, 0.12);
                border: 2px solid rgba(100, 116, 139, 0.3);
                box-shadow: 0 8px 32px rgba(100, 116, 139, 0.2);
            }
            
            .glass-negative {
                background: rgba(248, 113, 113, 0.12);
                border: 2px solid rgba(248, 113, 113, 0.3);
                box-shadow: 0 8px 32px rgba(248, 113, 113, 0.2);
            }
            
            .glass-strong-negative {
                background: rgba(239, 68, 68, 0.15);
                border: 2px solid rgba(239, 68, 68, 0.4);
                box-shadow: 0 8px 32px rgba(239, 68, 68, 0.3);
            }
            
            .classification-label {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #94a3b8;
                font-weight: 600;
                margin-bottom: 1rem;
            }
            
            .classification-value {
                font-size: 2.5rem;
                font-weight: 800;
                margin: 1rem 0;
                letter-spacing: -0.5px;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
            }
            
            .classification-desc {
                font-size: 0.95rem;
                color: #94a3b8;
                margin-top: 1rem;
                font-weight: 400;
                line-height: 1.5;
            }
            
            .strong-positive-impact { color: #10b981; }
            .positive-impact { color: #34d399; }
            .neutral-impact { color: #94a3b8; }
            .negative-impact { color: #f87171; }
            .strong-negative-impact { color: #ef4444; }
            
            .reasoning-box {
                background: rgba(15, 23, 42, 0.4);
                border-left: 4px solid #3b82f6;
                padding: 1.5rem 1.5rem 1.5rem 2rem;
                border-radius: 12px;
                margin: 0;
                position: relative;
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .reasoning-icon {
                position: absolute;
                top: 1.5rem;
                left: 1.5rem;
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
            }
            
            .reasoning-label {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #64748b;
                font-weight: 600;
                margin-bottom: 1rem;
                padding-left: 3rem;
            }
            
            .reasoning-text {
                font-size: 1.05rem;
                line-height: 1.8;
                color: #cbd5e1;
                font-weight: 400;
                padding-left: 3rem;
            }
            
            .section-header {
                font-size: 1.5rem;
                font-weight: 700;
                color: #f3f4f6;
                margin: 2.5rem 0 1.5rem 0;
                padding-bottom: 0.75rem;
                border-bottom: 2px solid rgba(51, 65, 85, 0.5);
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.8rem;
                font-weight: 700;
                color: #f3f4f6;
                animation: countUp 1s ease-out;
            }
            
            @keyframes countUp {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            [data-testid="stMetricLabel"] {
                color: #94a3b8;
                font-weight: 600;
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .warning-banner {
                background: linear-gradient(135deg, rgba(146, 64, 14, 0.2) 0%, rgba(180, 83, 9, 0.2) 100%);
                backdrop-filter: blur(10px);
                padding: 1rem 1.5rem;
                border-radius: 12px;
                border-left: 4px solid #f59e0b;
                margin: 1.5rem 0;
                color: #fef3c7;
                animation: pulseWarning 2s infinite;
            }
            
            @keyframes pulseWarning {
                0%, 100% { border-left-width: 4px; }
                50% { border-left-width: 6px; }
            }
            
            .info-banner {
                background: linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(30, 64, 175, 0.2) 100%);
                backdrop-filter: blur(10px);
                padding: 1rem 1.5rem;
                border-radius: 12px;
                border-left: 4px solid #3b82f6;
                margin: 1.5rem 0;
                color: #e0e7ff;
            }
            
            .recommendation-badge {
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                animation: fadeInScale 1s ease-out;
                border: 2px solid;
            }
            
            .badge-strong-buy {
                background: rgba(16, 185, 129, 0.15);
                border-color: rgba(16, 185, 129, 0.4);
            }
            
            .badge-buy {
                background: rgba(52, 211, 153, 0.12);
                border-color: rgba(52, 211, 153, 0.3);
            }
            
            .badge-neutral {
                background: rgba(100, 116, 139, 0.12);
                border-color: rgba(100, 116, 139, 0.3);
            }
            
            .badge-sell {
                background: rgba(248, 113, 113, 0.12);
                border-color: rgba(248, 113, 113, 0.3);
            }
            
            .badge-strong-sell {
                background: rgba(239, 68, 68, 0.15);
                border-color: rgba(239, 68, 68, 0.4);
            }
            
            .relevance-badge {
                display: inline-block;
                padding: 0.4rem 0.8rem;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                backdrop-filter: blur(10px);
            }
            
            .badge-high {
                background: rgba(5, 150, 105, 0.2);
                border: 1px solid rgba(5, 150, 105, 0.4);
                color: #059669;
            }
            
            .badge-medium {
                background: rgba(217, 119, 6, 0.2);
                border: 1px solid rgba(217, 119, 6, 0.4);
                color: #d97706;
            }
            
            .badge-low {
                background: rgba(220, 38, 38, 0.2);
                border: 1px solid rgba(220, 38, 38, 0.4);
                color: #dc2626;
            }
        </style>
        """
    else:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            * {
                font-family: 'Inter', sans-serif;
            }
            
            .stApp {
                background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
                color: #111827;
            }
            
            .hero-glass {
                background: rgba(255, 255, 255, 0.7);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(59, 130, 246, 0.2);
                border-radius: 24px;
                padding: 2.5rem;
                margin-bottom: 2rem;
                box-shadow: 0 8px 32px rgba(59, 130, 246, 0.1);
                animation: fadeInScale 0.6s ease-out;
            }
            
            @keyframes fadeInScale {
                from {
                    opacity: 0;
                    transform: scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }
            
            .main-header {
                font-size: 3rem;
                background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
                margin-bottom: 0.5rem;
                letter-spacing: -1.5px;
                line-height: 1.2;
            }
            
            .sub-text {
                font-size: 1.1rem;
                color: #64748b;
                margin-bottom: 0;
                font-weight: 400;
                line-height: 1.6;
            }
            
            .classification-glass {
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                animation: fadeInScale 0.8s ease-out;
                transition: all 0.3s ease;
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .classification-glass:hover {
                transform: translateY(-4px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            }
            
            .glass-strong-positive {
                background: rgba(5, 150, 105, 0.15);
                border: 2px solid rgba(5, 150, 105, 0.4);
                box-shadow: 0 8px 32px rgba(5, 150, 105, 0.3);
            }
            
            .glass-positive {
                background: rgba(16, 185, 129, 0.12);
                border: 2px solid rgba(16, 185, 129, 0.3);
                box-shadow: 0 8px 32px rgba(16, 185, 129, 0.2);
            }
            
            .glass-neutral {
                background: rgba(100, 116, 139, 0.12);
                border: 2px solid rgba(100, 116, 139, 0.3);
                box-shadow: 0 8px 32px rgba(100, 116, 139, 0.2);
            }
            
            .glass-negative {
                background: rgba(239, 68, 68, 0.12);
                border: 2px solid rgba(239, 68, 68, 0.3);
                box-shadow: 0 8px 32px rgba(239, 68, 68, 0.2);
            }
            
            .glass-strong-negative {
                background: rgba(220, 38, 38, 0.15);
                border: 2px solid rgba(220, 38, 38, 0.4);
                box-shadow: 0 8px 32px rgba(220, 38, 38, 0.3);
            }
            
            .classification-label {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #64748b;
                font-weight: 600;
                margin-bottom: 1rem;
            }
            
            .classification-value {
                font-size: 2.5rem;
                font-weight: 800;
                margin: 1rem 0;
                letter-spacing: -0.5px;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
            }
            
            .classification-desc {
                font-size: 0.95rem;
                color: #64748b;
                margin-top: 1rem;
                font-weight: 400;
                line-height: 1.5;
            }
            
            .strong-positive-impact { color: #059669; }
            .positive-impact { color: #10b981; }
            .neutral-impact { color: #64748b; }
            .negative-impact { color: #ef4444; }
            .strong-negative-impact { color: #dc2626; }
            
            .reasoning-box {
                background: rgba(248, 250, 252, 0.6);
                border-left: 4px solid #2563eb;
                padding: 1.5rem 1.5rem 1.5rem 2rem;
                border-radius: 12px;
                margin: 0;
                position: relative;
                min-height: 280px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .reasoning-icon {
                position: absolute;
                top: 1.5rem;
                left: 1.5rem;
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
            }
            
            .reasoning-label {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #64748b;
                font-weight: 600;
                margin-bottom: 1rem;
                padding-left: 3rem;
            }
            
            .reasoning-text {
                font-size: 1.05rem;
                line-height: 1.8;
                color: #334155;
                font-weight: 400;
                padding-left: 3rem;
            }
            
            .section-header {
                font-size: 1.5rem;
                font-weight: 700;
                color: #111827;
                margin: 2.5rem 0 1.5rem 0;
                padding-bottom: 0.75rem;
                border-bottom: 2px solid rgba(226, 232, 240, 0.8);
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.8rem;
                font-weight: 700;
                color: #111827;
                animation: countUp 1s ease-out;
            }
            
            @keyframes countUp {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            [data-testid="stMetricLabel"] {
                color: #64748b;
                font-weight: 600;
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .warning-banner {
                background: linear-gradient(135deg, rgba(254, 243, 199, 0.8) 0%, rgba(253, 230, 138, 0.8) 100%);
                backdrop-filter: blur(10px);
                padding: 1rem 1.5rem;
                border-radius: 12px;
                border-left: 4px solid #f59e0b;
                margin: 1.5rem 0;
                color: #92400e;
                animation: pulseWarning 2s infinite;
            }
            
            @keyframes pulseWarning {
                0%, 100% { border-left-width: 4px; }
                50% { border-left-width: 6px; }
            }
            
            .info-banner {
                background: linear-gradient(135deg, rgba(219, 234, 254, 0.8) 0%, rgba(191, 219, 254, 0.8) 100%);
                backdrop-filter: blur(10px);
                padding: 1rem 1.5rem;
                border-radius: 12px;
                border-left: 4px solid #2563eb;
                margin: 1.5rem 0;
                color: #1e40af;
            }
            
            .recommendation-badge {
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                animation: fadeInScale 1s ease-out;
                border: 2px solid;
            }
            
            .badge-strong-buy {
                background: rgba(5, 150, 105, 0.15);
                border-color: rgba(5, 150, 105, 0.4);
            }
            
            .badge-buy {
                background: rgba(16, 185, 129, 0.12);
                border-color: rgba(16, 185, 129, 0.3);
            }
            
            .badge-neutral {
                background: rgba(100, 116, 139, 0.12);
                border-color: rgba(100, 116, 139, 0.3);
            }
            
            .badge-sell {
                background: rgba(239, 68, 68, 0.12);
                border-color: rgba(239, 68, 68, 0.3);
            }
            
            .badge-strong-sell {
                background: rgba(220, 38, 38, 0.15);
                border-color: rgba(220, 38, 38, 0.4);
            }
            
            .relevance-badge {
                display: inline-block;
                padding: 0.4rem 0.8rem;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                backdrop-filter: blur(10px);
            }
            
            .badge-high {
                background: rgba(5, 150, 105, 0.2);
                border: 1px solid rgba(5, 150, 105, 0.4);
                color: #059669;
            }
            
            .badge-medium {
                background: rgba(217, 119, 6, 0.2);
                border: 1px solid rgba(217, 119, 6, 0.4);
                color: #d97706;
            }
            
            .badge-low {
                background: rgba(220, 38, 38, 0.2);
                border: 1px solid rgba(220, 38, 38, 0.4);
                color: #dc2626;
            }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

# SIDEBAR
with st.sidebar:
    st.markdown("### Settings")
    
    theme_label = "Switch to Dark Mode" if st.session_state["theme"] == "light" else "Switch to Light Mode"
    if st.button(theme_label, use_container_width=True, key="theme_toggle"):
        toggle_theme()
        st.rerun()
    
    st.divider()
    
    st.markdown("### Quick Actions")
    
    if st.button("How to Use This App", use_container_width=True, key="show_guide_btn"):
        st.session_state["show_guide"] = not st.session_state["show_guide"]
    
    st.divider()
    
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
    
    with st.expander("About This Application"):
        st.markdown("""
        **Version:** 3.0 Professional
        
        **Core Features:**
        - AI-powered sentiment analysis with FinBERT
        - 5-tier classification system
        - Relevance detection algorithm
        - Real-time stock data integration
        - Technical indicators & risk metrics
        - Historical comparison tools
        - Glassmorphic UI design
        - Analysis history tracking
        
        **Powered By:**
        - FinBERT (Financial Sentiment)
        - Yahoo Finance API
        - Plotly Visualization
        """)

# HERO GLASSMORPHIC CARD
st.markdown("""
<div class="hero-glass">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex: 1;">
            <h1 class="main-header">Finance News Impact Simulator</h1>
            <p class="sub-text">Advanced AI-powered sentiment analysis with relevance detection and 5-tier classification system</p>
        </div>
        <div>
""", unsafe_allow_html=True)

if st.button("Logout", type="secondary", key="logout_btn"):
    st.session_state["logged_in"] = False
    st.session_state.clear()
    st.rerun()

st.markdown("""
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# HOW TO USE GUIDE
if st.session_state["show_guide"]:
    st.markdown("""
    <div class="guide-box">
        <div class="guide-step">
            <div class="step-number">1</div>
            <div class="step-content">
                <h4>Enter Stock Ticker</h4>
                <p>Input the stock symbol you want to analyze (e.g., AAPL for Apple, TSLA for Tesla). You can also add a comparison ticker like SPY for benchmarking.</p>
            </div>
        </div>
        <div class="guide-step">
            <div class="step-number">2</div>
            <div class="step-content">
                <h4>Select Time Range</h4>
                <p>Choose the historical data period from 1 month to 5 years. This determines how much historical price data will be displayed in the charts.</p>
            </div>
        </div>
        <div class="guide-step">
            <div class="step-number">3</div>
            <div class="step-content">
                <h4>Input News Headline</h4>
                <p>Paste or type any financial news headline you want to analyze. The AI will automatically detect sentiment and relevance to your chosen ticker.</p>
            </div>
        </div>
        <div class="guide-step">
            <div class="step-number">4</div>
            <div class="step-content">
                <h4>Analyze with AI</h4>
                <p>Click "Analyze with AI" to process the headline. The system will analyze sentiment, check relevance, fetch stock data, and generate comprehensive insights.</p>
            </div>
        </div>
        <div class="guide-step">
            <div class="step-number">5</div>
            <div class="step-content">
                <h4>Interpret Results</h4>
                <p>Review the classification (Strong Buy/Buy/Neutral/Sell/Strong Sell), confidence scores, technical indicators, and AI-powered trading recommendations.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# SIMULATION PARAMETERS
st.markdown('<h2 class="section-header">Simulation Parameters</h2>', unsafe_allow_html=True)

config_col1, config_col2, config_col3 = st.columns([3, 3, 3])

with config_col1:
    ticker = st.text_input(
        "Stock Ticker Symbol", 
        value="TSLA", 
        help="Enter standard ticker symbols (e.g., AAPL, MSFT, RELIANCE.NS)"
    ).upper()
    
with config_col2:
    period = st.selectbox(
        "Time Range", 
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], 
        index=3,
        help="Select how far back to pull stock data"
    )

with config_col3:
    comparison_ticker = st.text_input(
        "Benchmark Against (Optional)",
        value="",
        placeholder="e.g., SPY",
        help="Add a benchmark ticker for comparison"
    ).upper()

# NEWS ANALYSIS INPUT
st.markdown('<h2 class="section-header">News Headline Analysis</h2>', unsafe_allow_html=True)

headline_input = st.text_area(
    "Enter News Headline", 
    height=120, 
    placeholder="Example: Federal Reserve unexpectedly cuts interest rates by 50 basis points...",
    help="Enter any financial news headline to analyze its potential market impact"
)

col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 7])
with col_btn1:
    analyze_button = st.button("Analyze with AI", type="primary", use_container_width=True)

def get_plotly_theme():
    if st.session_state["theme"] == "dark":
        return {
            "template": "plotly_dark",
            "paper_bgcolor": "#0f172a",
            "plot_bgcolor": "#1e293b",
            "font_color": "#e8eaed",
            "grid_color": "#334155"
        }
    else:
        return {
            "template": "plotly_white",
            "paper_bgcolor": "#ffffff",
            "plot_bgcolor": "#f9fafb",
            "font_color": "#111827",
            "grid_color": "#e5e7eb"
        }

def get_category_info(category):
    category_map = {
        'STRONG_POSITIVE': {
            'class': 'strong-positive-impact',
            'glass_class': 'glass-strong-positive',
            'badge_class': 'badge-strong-buy',
            'delta_color': 'normal',
            'icon': 'STRONG BUY',
            'description': 'Significant positive impact expected with high confidence'
        },
        'POSITIVE': {
            'class': 'positive-impact',
            'glass_class': 'glass-positive',
            'badge_class': 'badge-buy',
            'delta_color': 'normal',
            'icon': 'BUY',
            'description': 'Moderate positive impact likely'
        },
        'NEUTRAL': {
            'class': 'neutral-impact',
            'glass_class': 'glass-neutral',
            'badge_class': 'badge-neutral',
            'delta_color': 'off',
            'icon': 'NEUTRAL',
            'description': 'No significant market impact expected'
        },
        'NEGATIVE': {
            'class': 'negative-impact',
            'glass_class': 'glass-negative',
            'badge_class': 'badge-sell',
            'delta_color': 'inverse',
            'icon': 'SELL',
            'description': 'Moderate negative impact likely'
        },
        'STRONG_NEGATIVE': {
            'class': 'strong-negative-impact',
            'glass_class': 'glass-strong-negative',
            'badge_class': 'badge-strong-sell',
            'delta_color': 'inverse',
            'icon': 'STRONG SELL',
            'description': 'Significant negative impact expected with high confidence'
        }
    }
    return category_map.get(category, category_map['NEUTRAL'])

def get_relevance_badge(score):
    if score >= 0.7:
        return '<span class="relevance-badge badge-high">High Relevance</span>'
    elif score >= 0.4:
        return '<span class="relevance-badge badge-medium">Medium Relevance</span>'
    else:
        return '<span class="relevance-badge badge-low">Low Relevance</span>'

if analyze_button and headline_input.strip():
    show_analysis_progress()
    try:
        result = analyze_headline(headline_input, ticker=ticker, use_enhanced=True)
        stock_df = get_stock_data(ticker, period)
        
        comparison_df = None
        if comparison_ticker:
            comparison_df = get_stock_data(comparison_ticker, period)
        
        st.session_state["current_analysis"] = {
            "result": result,
            "stock_df": stock_df,
            "comparison_df": comparison_df,
            "ticker": ticker,
            "period": period,
            "comparison_ticker": comparison_ticker,
            "headline": headline_input
        }
        
        history_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "headline": headline_input,
            "category": result['category'],
            "polarity": result['polarity'],
            "impact": result['impact'],
            "confidence": result['confidence'],
            "relevance_score": result['relevance_score'],
            "is_relevant": result['is_relevant']
        }
        st.session_state["analysis_history"].insert(0, history_entry)
        if len(st.session_state["analysis_history"]) > 50:
            st.session_state["analysis_history"] = st.session_state["analysis_history"][:50]
    
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")
        with st.expander("Debug Information"):
            st.exception(e)

if st.session_state["current_analysis"] is not None:
    analysis = st.session_state["current_analysis"]
    result = analysis["result"]
    stock_df = analysis["stock_df"]
    comparison_df = analysis["comparison_df"]
    ticker = analysis["ticker"]
    period = analysis["period"]
    comparison_ticker = analysis["comparison_ticker"]
    
    theme = get_plotly_theme()
    
    category = result['category']
    category_info = get_category_info(category)
    
    # ANALYSIS RESULTS HEADER
    st.markdown('<h2 class="section-header">Analysis Results</h2>', unsafe_allow_html=True)
    
    # CLASSIFICATION GLASSMORPHIC SQUARE (LEFT) + REASONING (RIGHT)
    class_col, reason_col = st.columns([1, 2])
    
    with class_col:
        st.markdown(f"""
        <div class="classification-glass {category_info['glass_class']}">
            <div class="classification-label">Market Classification</div>
            <div class="classification-value {category_info['class']}">{category_info['icon']}</div>
            <div class="classification-desc">{category_info['description']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with reason_col:
        st.markdown(f"""
        <div class="reasoning-box">
            <div class="reasoning-icon">AI</div>
            <div class="reasoning-label">AI Analysis Reasoning</div>
            <div class="reasoning-text">{result['reason']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Relevance Warning
    if not result['is_relevant']:
        st.markdown(f"""
        <div class="warning-banner">
            <strong>Low Relevance Detected:</strong> This news headline does not appear to be directly relevant to {ticker}. Market impact is expected to be minimal.
        </div>
        """, unsafe_allow_html=True)
    
    # Key Metrics Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric("Target Ticker", ticker)
    
    with kpi2:
        st.metric(
            "Sentiment Score", 
            f"{result['polarity']:.3f}",
            delta=f"{abs(result['polarity']):.3f}",
            delta_color=category_info['delta_color']
        )
    
    with kpi3:
        st.metric("Confidence Level", f"{result['confidence']*100:.1f}%")
    
    with kpi4:
        st.markdown(f"""
        <div style="text-align: left;">
            <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94a3b8; font-weight: 600; margin-bottom: 0.5rem;">Relevance Score</div>
            <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.3rem;">{result['relevance_score']*100:.1f}%</div>
            {get_relevance_badge(result['relevance_score'])}
        </div>
        """, unsafe_allow_html=True)
    
    # TABS FOR DETAILED ANALYSIS
    tab_impact, tab_technical, tab_comparison, tab_raw = st.tabs([
        "Market Impact & Recommendations", 
        "Technical Analysis", 
        "Comparison Analysis",
        "Raw Data"
    ])

    with tab_impact:
        if result['is_relevant'] and result['category'] != 'NEUTRAL':
            st.markdown("### AI-Powered Trading Recommendation")
            
            if stock_df is not None and len(stock_df) >= 20:
                returns = stock_df['Close'].pct_change().dropna()
                current_price = stock_df['Close'].iloc[-1]
                
                ma_20 = stock_df['Close'].rolling(window=20).mean().iloc[-1]
                ma_50 = stock_df['Close'].rolling(window=50).mean().iloc[-1] if len(stock_df) >= 50 else ma_20
                
                momentum_20d = ((current_price - stock_df['Close'].iloc[-21]) / stock_df['Close'].iloc[-21] * 100) if len(stock_df) >= 21 else 0
                
                rolling_std = stock_df['Close'].rolling(window=20).std().iloc[-1]
                upper_band = ma_20 + (2 * rolling_std)
                lower_band = ma_20 - (2 * rolling_std)
                
                recommendation_score = 0
                reasons = []
                
                if category == 'STRONG_POSITIVE':
                    recommendation_score += 3
                    reasons.append("Strong positive sentiment detected")
                elif category == 'POSITIVE':
                    recommendation_score += 2
                    reasons.append("Positive sentiment detected")
                elif category == 'STRONG_NEGATIVE':
                    recommendation_score -= 3
                    reasons.append("Strong negative sentiment detected")
                elif category == 'NEGATIVE':
                    recommendation_score -= 2
                    reasons.append("Negative sentiment detected")
                
                if result['confidence'] > 0.85:
                    recommendation_score += 1 if result['polarity'] > 0 else -1
                    reasons.append(f"High confidence level ({result['confidence']:.2%})")
                
                if momentum_20d > 5:
                    recommendation_score += 1
                    reasons.append("Strong positive momentum detected")
                elif momentum_20d < -5:
                    recommendation_score -= 1
                    reasons.append("Negative momentum trend")
                
                if current_price > upper_band:
                    recommendation_score -= 1
                    reasons.append("Price above upper Bollinger Band (potentially overbought)")
                elif current_price < lower_band:
                    recommendation_score += 1
                    reasons.append("Price below lower Bollinger Band (potentially oversold)")
                
                rec_col1, rec_col2 = st.columns([1, 2])
                
                with rec_col1:
                    if recommendation_score >= 4:
                        recommendation = "STRONG BUY"
                        rec_color = "#10b981"
                        badge_class = "badge-strong-buy"
                    elif recommendation_score >= 2:
                        recommendation = "BUY"
                        rec_color = "#34d399"
                        badge_class = "badge-buy"
                    elif recommendation_score <= -4:
                        recommendation = "STRONG SELL"
                        rec_color = "#ef4444"
                        badge_class = "badge-strong-sell"
                    elif recommendation_score <= -2:
                        recommendation = "SELL"
                        rec_color = "#f87171"
                        badge_class = "badge-sell"
                    else:
                        recommendation = "NEUTRAL"
                        rec_color = "#94a3b8"
                        badge_class = "badge-neutral"
                    
                    st.markdown(f"""
                    <div class="recommendation-badge {badge_class}">
                        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; color: #94a3b8; margin-bottom: 0.5rem;">Recommendation</div>
                        <div style="font-size: 2.5rem; font-weight: 800; color: {rec_color}; margin: 1rem 0;">{recommendation}</div>
                        <div style="font-size: 0.9rem; color: #94a3b8;">Confidence Score: {abs(recommendation_score)}/6</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with rec_col2:
                    st.markdown("**Key Decision Factors:**")
                    for reason in reasons:
                        st.markdown(f"- {reason}")
                    
                    st.markdown("""
                    <div class="info-banner" style="margin-top: 1rem;">
                        <strong>Disclaimer:</strong> This is AI-generated analysis for educational purposes only and not financial advice. Always conduct thorough research and consult with financial professionals before making investment decisions.
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if stock_df is not None and len(stock_df) > 1:
            st.markdown("### Price Movement & Volume Analysis")
            
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=('Price Chart (OHLC)', 'Trading Volume')
            )
            
            fig.add_trace(
                go.Candlestick(
                    x=stock_df['Date'],
                    open=stock_df['Open'],
                    high=stock_df['High'],
                    low=stock_df['Low'],
                    close=stock_df['Close'],
                    name='OHLC',
                    increasing_line_color='#10b981',
                    decreasing_line_color='#ef4444'
                ),
                row=1, col=1
            )
            
            if len(stock_df) >= 20:
                stock_df['MA20'] = stock_df['Close'].rolling(window=20).mean()
                fig.add_trace(
                    go.Scatter(
                        x=stock_df['Date'], 
                        y=stock_df['MA20'], 
                        mode='lines', 
                        name='20-Day MA',
                        line=dict(color='#f59e0b', width=2)
                    ),
                    row=1, col=1
                )
            
            if len(stock_df) >= 50:
                stock_df['MA50'] = stock_df['Close'].rolling(window=50).mean()
                fig.add_trace(
                    go.Scatter(
                        x=stock_df['Date'], 
                        y=stock_df['MA50'], 
                        mode='lines', 
                        name='50-Day MA',
                        line=dict(color='#8b5cf6', width=2)
                    ),
                    row=1, col=1
                )
            
            colors = ['#10b981' if stock_df['Close'].iloc[i] >= stock_df['Open'].iloc[i] else '#ef4444' 
                      for i in range(len(stock_df))]
            
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
            
            fig.update_layout(
                template=theme['template'],
                paper_bgcolor=theme['paper_bgcolor'],
                plot_bgcolor=theme['plot_bgcolor'],
                font_color=theme['font_color'],
                height=600,
                hovermode="x unified",
                margin=dict(l=0, r=0, t=40, b=0),
                showlegend=True,
                xaxis_rangeslider_visible=False
            )
            
            fig.update_xaxes(gridcolor=theme['grid_color'])
            fig.update_yaxes(gridcolor=theme['grid_color'])
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Market Statistics")
            stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
            
            with stat_col1:
                current_price = stock_df['Close'].iloc[-1]
                prev_close = stock_df['Close'].iloc[-2] if len(stock_df) > 1 else current_price
                change_pct = ((current_price - prev_close) / prev_close) * 100
                st.metric("Current Price", f"${current_price:.2f}", delta=f"{change_pct:+.2f}%")
            
            with stat_col2:
                day_high = stock_df['High'].iloc[-1]
                st.metric("Day High", f"${day_high:.2f}")
            
            with stat_col3:
                day_low = stock_df['Low'].iloc[-1]
                st.metric("Day Low", f"${day_low:.2f}")
            
            with stat_col4:
                avg_volume = stock_df['Volume'].mean()
                current_volume = stock_df['Volume'].iloc[-1]
                volume_change = ((current_volume - avg_volume) / avg_volume) * 100
                st.metric("Volume", f"{current_volume/1e6:.2f}M", delta=f"{volume_change:+.1f}%")
            
            with stat_col5:
                period_return = ((stock_df['Close'].iloc[-1] - stock_df['Close'].iloc[0]) / stock_df['Close'].iloc[0]) * 100
                st.metric(f"{period} Return", f"{period_return:+.2f}%")

    with tab_technical:
        if stock_df is not None and len(stock_df) >= 20:
            st.markdown("### Technical Indicators")
            
            stock_df['Returns'] = stock_df['Close'].pct_change()
            stock_df['Cumulative_Returns'] = (1 + stock_df['Returns']).cumprod() - 1
            
            delta = stock_df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            stock_df['RSI'] = 100 - (100 / (1 + rs))
            
            rolling_mean = stock_df['Close'].rolling(window=20).mean()
            rolling_std = stock_df['Close'].rolling(window=20).std()
            stock_df['Upper_BB'] = rolling_mean + (2 * rolling_std)
            stock_df['Lower_BB'] = rolling_mean - (2 * rolling_std)
            
            tech_col1, tech_col2 = st.columns(2)
            
            with tech_col1:
                fig_bb = go.Figure()
                
                fig_bb.add_trace(go.Scatter(
                    x=stock_df['Date'],
                    y=stock_df['Upper_BB'],
                    name='Upper Band',
                    line=dict(color='#ef4444', width=1, dash='dash'),
                    mode='lines'
                ))
                
                fig_bb.add_trace(go.Scatter(
                    x=stock_df['Date'],
                    y=stock_df['Close'],
                    name='Close Price',
                    line=dict(color='#3b82f6', width=2),
                    fill='tonexty',
                    fillcolor='rgba(59, 130, 246, 0.1)'
                ))
                
                fig_bb.add_trace(go.Scatter(
                    x=stock_df['Date'],
                    y=stock_df['Lower_BB'],
                    name='Lower Band',
                    line=dict(color='#10b981', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(59, 130, 246, 0.1)'
                ))
                
                fig_bb.update_layout(
                    title="Bollinger Bands (20-day, 2 sigma)",
                    template=theme['template'],
                    paper_bgcolor=theme['paper_bgcolor'],
                    plot_bgcolor=theme['plot_bgcolor'],
                    font_color=theme['font_color'],
                    height=400,
                    xaxis=dict(gridcolor=theme['grid_color']),
                    yaxis=dict(gridcolor=theme['grid_color'])
                )
                st.plotly_chart(fig_bb, use_container_width=True)
            
            with tech_col2:
                fig_rsi = go.Figure()
                
                fig_rsi.add_trace(go.Scatter(
                    x=stock_df['Date'],
                    y=stock_df['RSI'],
                    mode='lines',
                    name='RSI',
                    line=dict(color='#3b82f6', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(59, 130, 246, 0.2)'
                ))
                
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444", annotation_text="Overbought (70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="#10b981", annotation_text="Oversold (30)")
                fig_rsi.add_hline(y=50, line_dash="dot", line_color="#6b7280", annotation_text="Neutral (50)")
                
                fig_rsi.update_layout(
                    title="Relative Strength Index (14-day)",
                    template=theme['template'],
                    paper_bgcolor=theme['paper_bgcolor'],
                    plot_bgcolor=theme['plot_bgcolor'],
                    font_color=theme['font_color'],
                    height=400,
                    yaxis=dict(range=[0, 100], gridcolor=theme['grid_color']),
                    xaxis=dict(gridcolor=theme['grid_color'])
                )
                st.plotly_chart(fig_rsi, use_container_width=True)
            
            st.markdown("### Risk & Performance Metrics")
            
            risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)
            
            returns = stock_df['Returns'].dropna()
            daily_volatility = returns.std()
            annual_volatility = daily_volatility * (252 ** 0.5)
            sharpe_ratio = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() != 0 else 0
            max_drawdown = ((stock_df['Close'] / stock_df['Close'].cummax()) - 1).min() * 100
            
            with risk_col1:
                st.metric("Daily Volatility", f"{daily_volatility*100:.2f}%")
                st.caption("Standard deviation of daily returns")
            
            with risk_col2:
                st.metric("Annual Volatility", f"{annual_volatility*100:.2f}%")
                st.caption("Annualized volatility (252 trading days)")
            
            with risk_col3:
                st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                st.caption("Risk-adjusted return measure")
            
            with risk_col4:
                st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
                st.caption("Largest peak-to-trough decline")
            
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=stock_df['Date'],
                y=stock_df['Cumulative_Returns'] * 100,
                mode='lines',
                fill='tozeroy',
                name='Cumulative Returns',
                line=dict(color='#3b82f6', width=2),
                fillcolor='rgba(59, 130, 246, 0.2)'
            ))
            
            fig_cum.update_layout(
                title=f"Cumulative Returns Over {period}",
                template=theme['template'],
                paper_bgcolor=theme['paper_bgcolor'],
                plot_bgcolor=theme['plot_bgcolor'],
                font_color=theme['font_color'],
                height=400,
                yaxis_title="Cumulative Return (%)",
                xaxis_title="Date",
                xaxis=dict(gridcolor=theme['grid_color']),
                yaxis=dict(gridcolor=theme['grid_color'])
            )
            st.plotly_chart(fig_cum, use_container_width=True)
        else:
            st.warning("Insufficient data for technical analysis. Need at least 20 data points.")

    with tab_comparison:
        if comparison_ticker and comparison_df is not None:
            st.markdown(f"### Performance Comparison: {ticker} vs {comparison_ticker}")
            
            min_len = min(len(stock_df), len(comparison_df))
            stock_normalized = (stock_df['Close'].iloc[:min_len] / stock_df['Close'].iloc[0]) * 100
            comparison_normalized = (comparison_df['Close'].iloc[:min_len] / comparison_df['Close'].iloc[0]) * 100
            
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Scatter(
                x=stock_df['Date'].iloc[:min_len],
                y=stock_normalized,
                mode='lines',
                name=ticker,
                line=dict(color='#3b82f6', width=3)
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=comparison_df['Date'].iloc[:min_len],
                y=comparison_normalized,
                mode='lines',
                name=comparison_ticker,
                line=dict(color='#f59e0b', width=3)
            ))
            
            fig_comp.update_layout(
                title="Normalized Price Comparison (Base = 100)",
                template=theme['template'],
                paper_bgcolor=theme['paper_bgcolor'],
                plot_bgcolor=theme['plot_bgcolor'],
                font_color=theme['font_color'],
                height=500,
                hovermode="x unified",
                yaxis_title="Normalized Price",
                xaxis_title="Date",
                xaxis=dict(gridcolor=theme['grid_color']),
                yaxis=dict(gridcolor=theme['grid_color'])
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
            perf_col1, perf_col2, perf_col3 = st.columns(3)
            
            ticker_return = ((stock_df['Close'].iloc[min_len-1] - stock_df['Close'].iloc[0]) / stock_df['Close'].iloc[0]) * 100
            comp_return = ((comparison_df['Close'].iloc[min_len-1] - comparison_df['Close'].iloc[0]) / comparison_df['Close'].iloc[0]) * 100
            outperformance = ticker_return - comp_return
            
            with perf_col1:
                st.metric(f"{ticker} Return", f"{ticker_return:.2f}%")
            with perf_col2:
                st.metric(f"{comparison_ticker} Return", f"{comp_return:.2f}%")
            with perf_col3:
                st.metric("Outperformance", f"{outperformance:.2f}%", delta=f"{outperformance:.2f}%")
            
            st.markdown("### Correlation Analysis")
            
            stock_returns = stock_df['Close'].iloc[:min_len].pct_change().dropna()
            comp_returns = comparison_df['Close'].iloc[:min_len].pct_change().dropna()
            
            min_returns_len = min(len(stock_returns), len(comp_returns))
            correlation = stock_returns.iloc[:min_returns_len].corr(comp_returns.iloc[:min_returns_len])
            
            corr_col1, corr_col2 = st.columns(2)
            
            with corr_col1:
                st.metric("Correlation Coefficient", f"{correlation:.3f}")
                if abs(correlation) > 0.7:
                    st.caption("Strong correlation - assets move together")
                elif abs(correlation) > 0.3:
                    st.caption("Moderate correlation")
                else:
                    st.caption("Weak correlation - diversification benefit")
            
            with corr_col2:
                fig_scatter = go.Figure()
                fig_scatter.add_trace(go.Scatter(
                    x=comp_returns.iloc[:min_returns_len] * 100,
                    y=stock_returns.iloc[:min_returns_len] * 100,
                    mode='markers',
                    marker=dict(color='#3b82f6', size=5, opacity=0.6),
                    name='Daily Returns'
                ))
                
                fig_scatter.update_layout(
                    title=f"Returns Correlation",
                    template=theme['template'],
                    paper_bgcolor=theme['paper_bgcolor'],
                    plot_bgcolor=theme['plot_bgcolor'],
                    font_color=theme['font_color'],
                    height=300,
                    xaxis_title=f"{comparison_ticker} Daily Return (%)",
                    yaxis_title=f"{ticker} Daily Return (%)",
                    xaxis=dict(gridcolor=theme['grid_color']),
                    yaxis=dict(gridcolor=theme['grid_color'])
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        elif comparison_ticker:
            st.warning(f"Could not fetch data for comparison ticker: {comparison_ticker}")
        else:
            st.info("Enter a comparison ticker in the parameters above to see side-by-side analysis")

    with tab_raw:
        st.markdown("### Raw Analysis Data")
        
        col_json1, col_json2 = st.columns(2)
        
        with col_json1:
            st.markdown("**Sentiment Analysis Results:**")
            analysis_data = {
                'category': result['category'],
                'polarity': result['polarity'],
                'confidence': result['confidence'],
                'relevance_score': result['relevance_score'],
                'is_relevant': result['is_relevant'],
                'reason': result['reason'],
                'raw_sentiment': result.get('raw_sentiment', 'N/A')
            }
            st.json(analysis_data)
        
        with col_json2:
            st.markdown("**Stock Data Summary:**")
            if stock_df is not None:
                summary_data = {
                    "ticker": ticker,
                    "period": period,
                    "data_points": len(stock_df),
                    "date_range": f"{stock_df['Date'].iloc[0]} to {stock_df['Date'].iloc[-1]}",
                    "price_range": f"${stock_df['Low'].min():.2f} - ${stock_df['High'].max():.2f}",
                    "latest_close": f"${stock_df['Close'].iloc[-1]:.2f}",
                    "total_volume": f"{stock_df['Volume'].sum()/1e9:.2f}B"
                }
                st.json(summary_data)
        
        if stock_df is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Export Options")
            
            csv_stock = stock_df.to_csv(index=False)
            st.download_button(
                label=f"Download {ticker} Stock Data (CSV)",
                data=csv_stock,
                file_name=f"{ticker}_{period}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

elif analyze_button and not headline_input.strip():
    st.warning("Please enter a headline to analyze.")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("Data Source: Yahoo Finance API")
with footer_col2:
    st.caption("AI Models: FinBERT & DistilBERT")
with footer_col3:
    st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")