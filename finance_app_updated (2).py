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
import io
from PIL import Image


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
if "auto_refresh" not in st.session_state:
    st.session_state["auto_refresh"] = True
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = datetime.now()
if "sentiment_history" not in st.session_state:
    st.session_state["sentiment_history"] = {}
if "price_alerts" not in st.session_state:
    st.session_state["price_alerts"] = []

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

def clear_analysis():
    st.session_state["current_analysis"] = None

def detect_candlestick_patterns(stock_df):
    patterns = []
    if len(stock_df) < 3:
        return patterns
    
    for i in range(2, len(stock_df)):
        open_price = stock_df['Open'].iloc[i]
        close_price = stock_df['Close'].iloc[i]
        high_price = stock_df['High'].iloc[i]
        low_price = stock_df['Low'].iloc[i]
        
        prev_open = stock_df['Open'].iloc[i-1]
        prev_close = stock_df['Close'].iloc[i-1]
        
        body = abs(close_price - open_price)
        range_val = high_price - low_price
        
        # Doji pattern
        if range_val > 0 and body / range_val < 0.1:
            patterns.append({
                'date': stock_df['Date'].iloc[i],
                'pattern': 'Doji',
                'type': 'Neutral',
                'description': 'Indecision in the market'
            })
        
        # Hammer pattern
        upper_shadow = high_price - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low_price
        if body > 0 and lower_shadow > 2 * body and upper_shadow < body:
            patterns.append({
                'date': stock_df['Date'].iloc[i],
                'pattern': 'Hammer',
                'type': 'Bullish',
                'description': 'Potential reversal to upside'
            })
        
        # Shooting Star
        if body > 0 and upper_shadow > 2 * body and lower_shadow < body:
            patterns.append({
                'date': stock_df['Date'].iloc[i],
                'pattern': 'Shooting Star',
                'type': 'Bearish',
                'description': 'Potential reversal to downside'
            })
        
        # Bullish Engulfing
        if close_price > open_price and prev_close < prev_open:
            if open_price < prev_close and close_price > prev_open:
                patterns.append({
                    'date': stock_df['Date'].iloc[i],
                    'pattern': 'Bullish Engulfing',
                    'type': 'Bullish',
                    'description': 'Strong buying pressure'
                })
        
        # Bearish Engulfing
        if close_price < open_price and prev_close > prev_open:
            if open_price > prev_close and close_price < prev_open:
                patterns.append({
                    'date': stock_df['Date'].iloc[i],
                    'pattern': 'Bearish Engulfing',
                    'type': 'Bearish',
                    'description': 'Strong selling pressure'
                })
    
    return patterns[-5:] if len(patterns) > 5 else patterns

def detect_support_resistance(stock_df, window=20):
    levels = []
    
    if len(stock_df) < window:
        return levels
    
    for i in range(window, len(stock_df) - window):
        high_val = stock_df['High'].iloc[i]
        low_val = stock_df['Low'].iloc[i]
        
        # Check if it's a local maximum (resistance)
        if high_val == stock_df['High'].iloc[i-window:i+window].max():
            levels.append({'price': high_val, 'type': 'Resistance', 'strength': 1})
        
        # Check if it's a local minimum (support)
        if low_val == stock_df['Low'].iloc[i-window:i+window].min():
            levels.append({'price': low_val, 'type': 'Support', 'strength': 1})
    
    # Consolidate close levels
    consolidated = []
    for level in levels:
        found = False
        for cons in consolidated:
            if abs(level['price'] - cons['price']) / cons['price'] < 0.02:
                cons['strength'] += 1
                found = True
                break
        if not found:
            consolidated.append(level)
    
    # Sort by strength and return top levels
    consolidated.sort(key=lambda x: x['strength'], reverse=True)
    return consolidated[:5]

def track_sentiment_history(ticker, result):
    if ticker not in st.session_state["sentiment_history"]:
        st.session_state["sentiment_history"][ticker] = []
    
    st.session_state["sentiment_history"][ticker].append({
        'timestamp': datetime.now(),
        'polarity': result['polarity'],
        'category': result['category'],
        'confidence': result['confidence']
    })
    
    # Keep only last 50 entries
    if len(st.session_state["sentiment_history"][ticker]) > 50:
        st.session_state["sentiment_history"][ticker] = st.session_state["sentiment_history"][ticker][-50:]

def get_theme_css():
    if st.session_state["theme"] == "dark":
        return """
        <style>
            .stApp {
                background-color: #0a0e1a;
                color: #ffffff;
            }
            
            .main-header {
                font-size: 2.8rem;
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
                margin-bottom: 0;
                letter-spacing: -1px;
            }
            
            .sub-text {
                font-size: 1.15rem;
                color: #e5e7eb;
                margin-bottom: 2rem;
                font-weight: 400;
            }
            
            .section-header {
                font-size: 1.5rem;
                font-weight: 600;
                color: #ffffff;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
                border-bottom: 2px solid #1e293b;
                padding-bottom: 0.5rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 2rem;
                font-weight: 700;
                color: #ffffff;
            }
            
            [data-testid="stMetricLabel"] {
                color: #e5e7eb;
                font-weight: 500;
            }
            
            .metric-card {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #334155;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }
            
            .analysis-box {
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                padding: 1.5rem;
                border-radius: 10px;
                border: 1px solid #334155;
                margin: 1rem 0;
                color: #ffffff;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }
            
            .analysis-box-header {
                font-weight: 600;
                font-size: 0.95rem;
                color: #e5e7eb;
                margin-bottom: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .analysis-box-content {
                font-size: 1rem;
                line-height: 1.6;
                color: #f3f4f6;
            }
            
            .relevance-alert {
                background: linear-gradient(135deg, #422006 0%, #292524 100%);
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 4px solid #f59e0b;
                margin: 1rem 0;
                color: #fbbf24;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }
            
            .relevance-alert-header {
                font-weight: 600;
                font-size: 0.95rem;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .live-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                background-color: #065f46;
                color: #6ee7b7;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                margin-left: 0.5rem;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
            
            .pattern-badge {
                display: inline-block;
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                font-size: 0.85rem;
                font-weight: 600;
                margin: 0.25rem;
            }
            
            .pattern-bullish {
                background-color: #065f46;
                color: #6ee7b7;
            }
            
            .pattern-bearish {
                background-color: #7f1d1d;
                color: #fca5a5;
            }
            
            .pattern-neutral {
                background-color: #78350f;
                color: #fcd34d;
            }
            
            .strong-positive-impact { 
                color: #10b981; 
                font-weight: 700;
                font-size: 1.1rem;
            }
            .positive-impact { 
                color: #34d399; 
                font-weight: 600; 
            }
            .neutral-impact { 
                color: #fbbf24; 
                font-weight: 600; 
            }
            .negative-impact { 
                color: #f87171; 
                font-weight: 600; 
            }
            .strong-negative-impact { 
                color: #ef4444; 
                font-weight: 700;
                font-size: 1.1rem;
            }
            
            .dataframe {
                background-color: #1e293b !important;
                color: #ffffff !important;
            }
            
            .dataframe thead tr th {
                background-color: #0f172a !important;
                color: #ffffff !important;
                border-bottom: 2px solid #334155 !important;
                padding: 12px !important;
                font-weight: 600 !important;
            }
            
            .dataframe tbody tr td {
                background-color: #1e293b !important;
                color: #e5e7eb !important;
                border-bottom: 1px solid #334155 !important;
                padding: 10px !important;
            }
            
            .dataframe tbody tr:hover td {
                background-color: #334155 !important;
            }
            
            [data-testid="stDataFrame"] {
                background-color: #1e293b !important;
            }
            
            [data-testid="stDataFrame"] > div {
                background-color: #1e293b !important;
            }
            
            [data-testid="stJson"] {
                background-color: #1e293b !important;
                color: #ffffff !important;
                border: 1px solid #334155 !important;
                border-radius: 8px !important;
                padding: 1rem !important;
            }
            
            [data-testid="stJson"] pre {
                background-color: #0f172a !important;
                color: #ffffff !important;
            }
            
            .streamlit-expanderContent {
                background-color: #1e293b !important;
                border: 1px solid #334155 !important;
                color: #ffffff !important;
            }
            
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background-color: #0f172a;
                padding: 0.5rem;
                border-radius: 10px;
            }
            
            .stTabs [data-baseweb="tab"] {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 12px 24px;
                border: 1px solid #334155;
                color: #e5e7eb;
                font-weight: 500;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                border: none;
                color: #ffffff;
            }
            
            .stButton > button {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .stButton > button:hover {
                background-color: #334155;
                border-color: #475569;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
                transform: translateY(-1px);
            }
            
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
                color: #ffffff;
                border: none;
            }
            
            .stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, #2563eb 0%, #1e3a8a 100%);
                box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
                transform: translateY(-2px);
            }
            
            .stButton > button[kind="secondary"] {
                background-color: #7f1d1d;
                color: #fca5a5;
                border: 1px solid #991b1b;
            }
            
            .stButton > button[kind="secondary"]:hover {
                background-color: #991b1b;
                border-color: #b91c1c;
            }
            
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                background-color: #1e293b;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            
            [data-testid="stSidebar"] {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
            
            [data-testid="stSidebar"] * {
                color: #ffffff !important;
            }
            
            .streamlit-expanderHeader {
                background-color: #1e293b;
                color: #ffffff;
                border-radius: 8px;
                border: 1px solid #334155;
            }
            
            hr {
                border-color: #1e293b;
            }
            
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            
            ::-webkit-scrollbar-track {
                background: #0f172a;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #334155;
                border-radius: 5px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #475569;
            }
            
            .stMarkdown p, .stMarkdown li, .stMarkdown span {
                color: #ffffff !important;
            }
            
            .stCaption {
                color: #e5e7eb !important;
            }
        </style>
        """
    else:
        return """
        <style>
            .stApp {
                background-color: #ffffff;
                color: #111827;
            }
            
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
                color: #374151;
                margin-bottom: 2rem;
                font-weight: 400;
            }
            
            .section-header {
                font-size: 1.5rem;
                font-weight: 600;
                color: #111827;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 0.5rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 2rem;
                font-weight: 700;
                color: #111827;
            }
            
            [data-testid="stMetricLabel"] {
                color: #374151;
                font-weight: 500;
            }
            
            .metric-card {
                background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .analysis-box {
                background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
                padding: 1.5rem;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
                margin: 1rem 0;
                color: #111827;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            
            .analysis-box-header {
                font-weight: 600;
                font-size: 0.95rem;
                color: #374151;
                margin-bottom: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .analysis-box-content {
                font-size: 1rem;
                line-height: 1.6;
                color: #1f2937;
            }
            
            .relevance-alert {
                background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 4px solid #f59e0b;
                margin: 1rem 0;
                color: #92400e;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            
            .relevance-alert-header {
                font-weight: 600;
                font-size: 0.95rem;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .live-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                background-color: #d1fae5;
                color: #065f46;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                margin-left: 0.5rem;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .pattern-badge {
                display: inline-block;
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                font-size: 0.85rem;
                font-weight: 600;
                margin: 0.25rem;
            }
            
            .pattern-bullish {
                background-color: #d1fae5;
                color: #065f46;
            }
            
            .pattern-bearish {
                background-color: #fee2e2;
                color: #7f1d1d;
            }
            
            .pattern-neutral {
                background-color: #fef3c7;
                color: #78350f;
            }
            
            .strong-positive-impact { 
                color: #059669; 
                font-weight: 700;
                font-size: 1.1rem;
            }
            .positive-impact { 
                color: #10b981; 
                font-weight: 600; 
            }
            .neutral-impact { 
                color: #d97706; 
                font-weight: 600; 
            }
            .negative-impact { 
                color: #ef4444; 
                font-weight: 600; 
            }
            .strong-negative-impact { 
                color: #dc2626; 
                font-weight: 700;
                font-size: 1.1rem;
            }
            
            .dataframe {
                background-color: #ffffff !important;
                color: #111827 !important;
            }
            
            .dataframe thead tr th {
                background-color: #f9fafb !important;
                color: #111827 !important;
                border-bottom: 2px solid #e5e7eb !important;
                padding: 12px !important;
                font-weight: 600 !important;
            }
            
            .dataframe tbody tr td {
                background-color: #ffffff !important;
                color: #374151 !important;
                border-bottom: 1px solid #e5e7eb !important;
                padding: 10px !important;
            }
            
            .dataframe tbody tr:hover td {
                background-color: #f9fafb !important;
            }
            
            [data-testid="stDataFrame"] {
                background-color: #ffffff !important;
            }
            
            [data-testid="stDataFrame"] > div {
                background-color: #ffffff !important;
            }
            
            [data-testid="stJson"] {
                background-color: #f9fafb !important;
                color: #111827 !important;
                border: 1px solid #e5e7eb !important;
                border-radius: 8px !important;
                padding: 1rem !important;
            }
            
            [data-testid="stJson"] pre {
                background-color: #ffffff !important;
                color: #111827 !important;
            }
            
            .streamlit-expanderContent {
                background-color: #ffffff !important;
                border: 1px solid #e5e7eb !important;
                color: #111827 !important;
            }
            
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background-color: #f9fafb;
                padding: 0.5rem;
                border-radius: 10px;
            }
            
            .stTabs [data-baseweb="tab"] {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 12px 24px;
                border: 1px solid #e5e7eb;
                color: #374151;
                font-weight: 500;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                border: none;
                color: #ffffff;
            }
            
            .stButton > button {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            
            .stButton > button:hover {
                background-color: #f9fafb;
                border-color: #d1d5db;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
                transform: translateY(-1px);
            }
            
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                color: #ffffff;
                border: none;
            }
            
            .stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, #1d4ed8 0%, #6d28d9 100%);
                box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
                transform: translateY(-2px);
            }
            
            .stButton > button[kind="secondary"] {
                background-color: #fee2e2;
                color: #7f1d1d;
                border: 1px solid #fecaca;
            }
            
            .stButton > button[kind="secondary"]:hover {
                background-color: #fecaca;
                border-color: #fca5a5;
            }
            
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                background-color: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 8px;
            }
            
            [data-testid="stSidebar"] {
                background-color: #f9fafb;
                border-right: 1px solid #e5e7eb;
            }
            
            .streamlit-expanderHeader {
                background-color: #ffffff;
                color: #111827;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
            
            hr {
                border-color: #e5e7eb;
            }
            
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f9fafb;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #d1d5db;
                border-radius: 5px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #9ca3af;
            }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

if not st.session_state["logged_in"]:
    login_page()
    st.stop()

with st.sidebar:
    st.markdown("### Settings")
    
    theme_label = "Switch to Dark Mode" if st.session_state["theme"] == "light" else "Switch to Light Mode"
    if st.button(theme_label, use_container_width=True, key="theme_toggle"):
        toggle_theme()
        st.rerun()
    
    st.divider()
    
    st.markdown("### Recent Analyses")
    if st.session_state["analysis_history"]:
        for i, hist in enumerate(st.session_state["analysis_history"][-5:]):
            with st.expander(f"{hist['ticker']} - {hist['timestamp'][:10]}"):
                st.write(f"**Headline:** {hist['headline'][:60]}...")
                st.write(f"**Category:** {hist['category']}")
                st.write(f"**Impact:** {hist['impact']}")
                st.write(f"**Relevance:** {hist.get('relevance_score', 'N/A')}")
    else:
        st.info("No analysis history yet.")
    
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
        The Finance News Impact Simulator is an advanced AI-powered platform designed for institutional 
        investors, traders, and financial analysts. It combines state-of-the-art natural language processing 
        with real-time market data to evaluate the potential impact of news headlines on specific securities. 
        
        The system employs FinBERT sentiment analysis and relevance detection algorithms to provide 
        actionable intelligence with quantified confidence metrics. All analysis includes technical indicators, 
        historical comparisons, and risk assessments to support informed decision-making.
        
        This tool is designed for professional use and all outputs should be considered as analytical 
        support rather than direct investment advice.
        """)

col_nav1, col_nav2 = st.columns([8, 1])
with col_nav1:
    st.markdown('<div class="main-header">Finance News Impact Simulator</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">AI-powered sentiment analysis with relevance detection and 5-tier classification</p>', unsafe_allow_html=True)

with col_nav2:
    st.write("")
    st.write("")
    if st.button("Logout", type="secondary", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state.clear()
        st.rerun()

st.divider()

with st.container():
    st.markdown('<p class="section-header">Simulation Parameters</p>', unsafe_allow_html=True)
    config_col1, config_col2, config_col3 = st.columns([3, 3, 3])
    
    with config_col1:
        ticker = st.text_input(
            "Stock Ticker Symbol", 
            value="TSLA", 
            help="Enter standard ticker symbols (e.g., AAPL, MSFT, RELIANCE.NS)"
        ).upper()
        
    with config_col2:
        period = st.selectbox(
            "Historical Data Period", 
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y"], 
            index=3,
            help="Select how far back to pull stock data"
        )
    
    with config_col3:
        comparison_ticker = st.text_input(
            "Compare With (Optional)",
            value="",
            placeholder="e.g., SPY",
            help="Add a benchmark ticker for comparison"
        ).upper()

st.markdown('<p class="section-header">News Analysis</p>', unsafe_allow_html=True)

headline_input = st.text_area(
    "Enter News Headline for Simulation", 
    height=120, 
    placeholder="e.g., Federal Reserve unexpectedly cuts interest rates by 50 basis points...",
    help="Enter any news headline to analyze its potential market impact"
)

button_col1, button_col2, button_col3 = st.columns([2, 2, 8])
with button_col1:
    analyze_button = st.button("Run Analysis", type="primary", use_container_width=True)
with button_col2:
    if st.session_state["current_analysis"] is not None:
        if st.button("Clear Analysis", type="secondary", use_container_width=True):
            clear_analysis()
            st.rerun()

def get_plotly_theme():
    if st.session_state["theme"] == "dark":
        return {
            "template": "plotly_dark",
            "paper_bgcolor": "#0f172a",
            "plot_bgcolor": "#1e293b",
            "font_color": "#ffffff",
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
            'delta_color': 'normal',
            'icon': 'STRONG BUY',
            'description': 'Significant positive impact expected'
        },
        'POSITIVE': {
            'class': 'positive-impact',
            'delta_color': 'normal',
            'icon': 'BUY',
            'description': 'Moderate positive impact likely'
        },
        'NEUTRAL': {
            'class': 'neutral-impact',
            'delta_color': 'off',
            'icon': 'NEUTRAL',
            'description': 'No significant market impact expected'
        },
        'NEGATIVE': {
            'class': 'negative-impact',
            'delta_color': 'inverse',
            'icon': 'SELL',
            'description': 'Moderate negative impact likely'
        },
        'STRONG_NEGATIVE': {
            'class': 'strong-negative-impact',
            'delta_color': 'inverse',
            'icon': 'STRONG SELL',
            'description': 'Significant negative impact expected'
        }
    }
    return category_map.get(category, category_map['NEUTRAL'])

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
            "headline": headline_input,
            "timestamp": datetime.now()
        }
        
        track_sentiment_history(ticker, result)
        
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
        
        st.session_state["last_refresh"] = datetime.now()
        st.rerun()
    
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
    analysis_timestamp = analysis.get("timestamp", datetime.now())
    
    # Real-time refresh logic
    time_diff = datetime.now() - st.session_state["last_refresh"]
    seconds_ago = int(time_diff.total_seconds())
    
    if st.session_state["auto_refresh"] and seconds_ago >= 60:
        try:
            new_stock_df = get_stock_data(ticker, period)
            if new_stock_df is not None:
                st.session_state["current_analysis"]["stock_df"] = new_stock_df
                stock_df = new_stock_df
                st.session_state["last_refresh"] = datetime.now()
                st.rerun()
        except:
            pass
    
    # Display live badge and refresh controls
    refresh_col1, refresh_col2, refresh_col3 = st.columns([6, 2, 2])
    with refresh_col1:
        if seconds_ago < 60:
            st.markdown(f'<span class="live-badge">LIVE</span> <span style="color: {"#e5e7eb" if st.session_state["theme"] == "dark" else "#374151"};">Last updated: {seconds_ago}s ago</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color: {"#e5e7eb" if st.session_state["theme"] == "dark" else "#374151"};">Last updated: {seconds_ago}s ago</span>', unsafe_allow_html=True)
    
    with refresh_col2:
        if st.button("Refresh Now", use_container_width=True):
            try:
                new_stock_df = get_stock_data(ticker, period)
                if new_stock_df is not None:
                    st.session_state["current_analysis"]["stock_df"] = new_stock_df
                    st.session_state["last_refresh"] = datetime.now()
                    st.rerun()
            except:
                st.error("Failed to refresh data")
    
    with refresh_col3:
        auto_refresh_label = "Pause Auto" if st.session_state["auto_refresh"] else "Resume Auto"
        if st.button(auto_refresh_label, use_container_width=True):
            st.session_state["auto_refresh"] = not st.session_state["auto_refresh"]
            st.rerun()
    
    st.divider()
    
    theme = get_plotly_theme()
    
    category = result['category']
    category_info = get_category_info(category)
    
    # Detect patterns and support/resistance
    patterns = detect_candlestick_patterns(stock_df) if stock_df is not None else []
    support_resistance = detect_support_resistance(stock_df) if stock_df is not None else []
    
    tab_impact, tab_technical, tab_patterns, tab_sentiment, tab_comparison, tab_raw = st.tabs([
        "Market Impact", 
        "Technical Analysis",
        "Pattern Recognition",
        "Sentiment History",
        "Comparison",
        "Raw Data"
    ])

    with tab_impact:
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
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
            st.metric("Confidence", f"{result['confidence']*100:.1f}%")
        
        with kpi4:
            st.metric("Relevance", f"{result['relevance_score']*100:.1f}%")
        
        with kpi5:
            if stock_df is not None and len(stock_df) > 1:
                current_price = stock_df['Close'].iloc[-1]
                st.metric(f"Current Price", f"${current_price:.2f}")
        
        st.divider()
        
        col_cat1, col_cat2 = st.columns([1, 2])
        
        with col_cat1:
            st.markdown("**Classification:**")
            st.markdown(f"<p class='{category_info['class']}' style='font-size: 2rem; margin: 0;'>{category_info['icon']}</p>", unsafe_allow_html=True)
            st.caption(category_info['description'])
        
        with col_cat2:
            st.markdown("**Analysis Reasoning:**")
            st.markdown(f"""
                <div class="analysis-box">
                    <div class="analysis-box-header">Sentiment Analysis</div>
                    <div class="analysis-box-content">{result['reason']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if not result['is_relevant']:
                st.markdown(f"""
                    <div class="relevance-alert">
                        <div class="relevance-alert-header">Relevance Notice</div>
                        <div>This news headline does not appear to be directly relevant to {ticker}. Market impact is expected to be minimal.</div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        if result['is_relevant'] and result['category'] != 'NEUTRAL':
            st.markdown("#### AI-Powered Trading Recommendation")
            
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
                    reasons.append(f"High confidence ({result['confidence']:.2f})")
                
                if momentum_20d > 5:
                    recommendation_score += 1
                    reasons.append("Strong positive momentum")
                elif momentum_20d < -5:
                    recommendation_score -= 1
                    reasons.append("Negative momentum")
                
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
                    elif recommendation_score >= 2:
                        recommendation = "BUY"
                        rec_color = "#34d399"
                    elif recommendation_score <= -4:
                        recommendation = "STRONG SELL"
                        rec_color = "#ef4444"
                    elif recommendation_score <= -2:
                        recommendation = "SELL"
                        rec_color = "#f87171"
                    else:
                        recommendation = "NEUTRAL"
                        rec_color = "#fbbf24"
                    
                    st.markdown(f"<h2 style='color: {rec_color}; text-align: center;'>{recommendation}</h2>", unsafe_allow_html=True)
                    st.caption(f"Confidence Score: {abs(recommendation_score)}/6")
                
                with rec_col2:
                    st.markdown("**Key Factors:**")
                    for reason in reasons:
                        st.markdown(f"- {reason}")
                    
                    st.caption("Disclaimer: This is AI-generated analysis and not financial advice. Always conduct your own research.")
        
        st.divider()
        
        if stock_df is not None and len(stock_df) > 1:
            st.markdown("#### Price & Volume Analysis")
            
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=('Price Movement', 'Trading Volume')
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
            
            # Add support/resistance lines
            for level in support_resistance:
                color = '#ef4444' if level['type'] == 'Resistance' else '#10b981'
                fig.add_hline(
                    y=level['price'],
                    line_dash="dash",
                    line_color=color,
                    annotation_text=f"{level['type']}: ${level['price']:.2f}",
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
                        line=dict(color='#f59e0b', width=1.5)
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
                        line=dict(color='#8b5cf6', width=1.5)
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
            
            # Download chart button
            if st.button("Download Chart as PNG", key="download_price_chart"):
                st.info("Chart download feature - integrate with plotly kaleido for production")
            
            st.markdown("#### Real-Time Market Statistics")
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
            st.markdown("#### Technical Indicators & Risk Metrics")
            
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
                    title="Bollinger Bands (20-day, 2σ)",
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
            
            st.markdown("#### Risk & Performance Metrics")
            
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
    
    with tab_patterns:
        st.markdown("#### Candlestick Pattern Recognition")
        
        if patterns:
            st.markdown("**Detected Patterns (Last 5):**")
            for pattern in patterns:
                pattern_class = f"pattern-{pattern['type'].lower()}"
                st.markdown(f"""
                    <span class="pattern-badge {pattern_class}">
                        {pattern['pattern']} ({pattern['type']})
                    </span>
                    <span style="color: {"#e5e7eb" if st.session_state["theme"] == "dark" else "#374151"};">
                        {pattern['date']} - {pattern['description']}
                    </span>
                """, unsafe_allow_html=True)
                st.write("")
        else:
            st.info("No significant candlestick patterns detected in recent data.")
        
        st.divider()
        
        st.markdown("#### Support & Resistance Levels")
        
        if support_resistance:
            sr_df = pd.DataFrame(support_resistance)
            st.dataframe(sr_df[['type', 'price', 'strength']], use_container_width=True)
            st.caption("Strength indicates how many times the level has been tested")
        else:
            st.info("No clear support/resistance levels detected.")
    
    with tab_sentiment:
        st.markdown("#### Sentiment Analysis History")
        
        if ticker in st.session_state["sentiment_history"] and st.session_state["sentiment_history"][ticker]:
            history_data = st.session_state["sentiment_history"][ticker]
            
            # Create sentiment timeline
            hist_df = pd.DataFrame(history_data)
            
            fig_sentiment = go.Figure()
            
            fig_sentiment.add_trace(go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['polarity'],
                mode='lines+markers',
                name='Sentiment Polarity',
                line=dict(color='#3b82f6', width=2),
                marker=dict(size=8, color='#3b82f6')
            ))
            
            fig_sentiment.add_hline(y=0, line_dash="dash", line_color="#6b7280", annotation_text="Neutral")
            
            fig_sentiment.update_layout(
                title=f"Sentiment Timeline for {ticker}",
                template=theme['template'],
                paper_bgcolor=theme['paper_bgcolor'],
                plot_bgcolor=theme['plot_bgcolor'],
                font_color=theme['font_color'],
                height=400,
                yaxis_title="Sentiment Polarity",
                xaxis_title="Time",
                xaxis=dict(gridcolor=theme['grid_color']),
                yaxis=dict(gridcolor=theme['grid_color'], range=[-1, 1])
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)
            
            # Sentiment statistics
            st.markdown("#### Statistics")
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            avg_sentiment = hist_df['polarity'].mean()
            sentiment_std = hist_df['polarity'].std()
            avg_confidence = hist_df['confidence'].mean()
            total_analyses = len(hist_df)
            
            with stat_col1:
                st.metric("Average Sentiment", f"{avg_sentiment:.3f}")
            with stat_col2:
                st.metric("Sentiment Volatility", f"{sentiment_std:.3f}")
            with stat_col3:
                st.metric("Average Confidence", f"{avg_confidence*100:.1f}%")
            with stat_col4:
                st.metric("Total Analyses", total_analyses)
            
            # Category distribution
            category_counts = hist_df['category'].value_counts()
            fig_dist = go.Figure(data=[go.Pie(
                labels=category_counts.index,
                values=category_counts.values,
                hole=0.4
            )])
            
            fig_dist.update_layout(
                title="Sentiment Category Distribution",
                template=theme['template'],
                paper_bgcolor=theme['paper_bgcolor'],
                font_color=theme['font_color'],
                height=350
            )
            st.plotly_chart(fig_dist, use_container_width=True)
            
        else:
            st.info(f"No sentiment history available for {ticker}. Analyze more headlines to build history.")

    with tab_comparison:
        if comparison_ticker and comparison_df is not None:
            st.markdown(f"#### Performance Comparison: {ticker} vs {comparison_ticker}")
            
            min_len = min(len(stock_df), len(comparison_df))
            stock_normalized = (stock_df['Close'].iloc[:min_len] / stock_df['Close'].iloc[0]) * 100
            comparison_normalized = (comparison_df['Close'].iloc[:min_len] / comparison_df['Close'].iloc[0]) * 100
            
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Scatter(
                x=stock_df['Date'].iloc[:min_len],
                y=stock_normalized,
                mode='lines',
                name=ticker,
                line=dict(color='#3b82f6', width=2.5)
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=comparison_df['Date'].iloc[:min_len],
                y=comparison_normalized,
                mode='lines',
                name=comparison_ticker,
                line=dict(color='#f59e0b', width=2.5)
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
            
            st.divider()
            
            st.markdown("#### Correlation Analysis")
            
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
            st.markdown("""
                <div class="analysis-box">
                    <div class="analysis-box-header">Comparison Analysis</div>
                    <div class="analysis-box-content">Enter a comparison ticker in the parameters above to see side-by-side performance analysis and correlation metrics.</div>
                </div>
            """, unsafe_allow_html=True)

    with tab_raw:
        st.markdown("#### Raw Analysis Data")
        
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
        
        st.divider()
        
        st.markdown("**Similar Historical Headlines:**")
        if not result['matched'].empty:
            st.dataframe(result['matched'], use_container_width=True)
        else:
            st.markdown("""
                <div class="analysis-box">
                    <div class="analysis-box-content">No similar historical headlines found in the database.</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("**Export Options:**")
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if stock_df is not None:
                csv_stock = stock_df.to_csv(index=False)
                st.download_button(
                    label=f"Download Stock Data CSV",
                    data=csv_stock,
                    file_name=f"{ticker}_{period}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with export_col2:
            if stock_df is not None:
                # Create Excel file with multiple sheets
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    stock_df.to_excel(writer, sheet_name='Price Data', index=False)
                    pd.DataFrame([analysis_data]).to_excel(writer, sheet_name='Analysis', index=False)
                excel_buffer.seek(0)
                
                st.download_button(
                    label="Download Excel Report",
                    data=excel_buffer,
                    file_name=f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with export_col3:
            import json
            json_data = {
                'ticker': ticker,
                'analysis': analysis_data,
                'timestamp': datetime.now().isoformat(),
                'stock_summary': summary_data if stock_df is not None else {}
            }
            json_str = json.dumps(json_data, indent=2)
            
            st.download_button(
                label="Download JSON Data",
                data=json_str,
                file_name=f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

elif analyze_button and not headline_input.strip():
    st.warning("Please enter a headline to analyze.")

st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("Data provided by Yahoo Finance")
with footer_col2:
    st.caption("AI Analysis powered by FinBERT & DistilBERT")
with footer_col3:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh trigger (runs every time the app reruns)
if st.session_state["current_analysis"] is not None and st.session_state["auto_refresh"]:
    time.sleep(1)  # Small delay to prevent too frequent reruns
    time_since_refresh = (datetime.now() - st.session_state["last_refresh"]).total_seconds()
    if time_since_refresh >= 60:
        st.rerun()
    