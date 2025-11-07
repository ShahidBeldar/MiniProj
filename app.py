import streamlit as st
import plotly.express as px
from analyzer import analyze_headline
from utils import get_stock_data

st.set_page_config(page_title="Fake News Impact Simulator", layout="wide")

st.title(" Fake News Impact Simulator with Stock Charts")
st.markdown("Enter a fake news headline and choose a stock to simulate its impact.")

# --- Inputs ---
user_input = st.text_area(" Enter Fake News Headline")
ticker = st.text_input(" Enter Stock Ticker (e.g., TSLA, AAPL, INFY.NS, RELIANCE.NS)", "TSLA")
period = st.selectbox(" Time Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)

# --- Processing ---
if st.button("Analyze") and user_input.strip():
    result = analyze_headline(user_input)

    st.subheader("Analysis Results")
    st.write("**Sentiment Polarity:**", result['polarity'])
    st.write("**Predicted Impact:**", result['impact'])

    st.subheader(" Most Similar Real Headlines")
    st.dataframe(result['matched'])

    # --- Stock Chart ---
    st.subheader(f" Stock Price for {ticker.upper()} ({period})")
    stock_df = get_stock_data(ticker, period)
    if stock_df is not None:
        fig = px.line(stock_df, x="Date", y="Close", title=f"{ticker.upper()} Stock Price")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Could not fetch stock data for ticker: {ticker}")
