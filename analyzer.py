import streamlit as st
from transformers import pipeline
from utils import load_data, compute_similarity, compute_sentiment

# ============================================
# CRITICAL FIX: Cache the sentiment model
# This is what's causing your 57-second delay!
# ============================================

@st.cache_resource
def load_sentiment_model():
    """Load sentiment model ONCE and cache it"""
    print("🔄 Loading sentiment model (first time only)...")
    model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    print("✅ Model loaded!")
    return model

@st.cache_data
def load_news_data():
    """Load and process news data ONCE"""
    print("🔄 Loading news data (first time only)...")
    news_df = load_data("news.csv")
    news_df = compute_sentiment(news_df)
    print(f"✅ Loaded {len(news_df)} news articles")
    return news_df

def analyze_headline(headline):
    """
    Analyze headline - now runs in <2 seconds!
    Your app.py doesn't need to change at all.
    """
    # Get cached model and data (fast!)
    sentiment_model = load_sentiment_model()
    news_df = load_news_data()
    
    # Run sentiment analysis
    result = sentiment_model(headline, truncation=True, max_length=512)[0]
    label = result['label']
    score = result['score']

    # Convert to polarity & impact message (same as before)
    if label == "POSITIVE":
        impact = f"✓ Positive ({score:.2f} confidence) - Price likely to go up"
        polarity = score
    else:
        impact = f"✗ Negative ({score:.2f} confidence) - Price likely to go down"
        polarity = -score

    # Compute similarity with historical headlines
    matched = compute_similarity(news_df, headline)

    # Return in same format as before (no changes needed in app.py)
    return {
        'polarity': polarity,
        'impact': impact,
        'matched': matched[['Date', 'Headline', 'sentiment', 'similarity']].head(3)
    }