import streamlit as st
from transformers import pipeline
from utils import load_data, compute_similarity, compute_sentiment, compute_sentiment_enhanced

# CRITICAL FIX: Cache the sentiment models

@st.cache_resource
def load_sentiment_model():
    """Load old sentiment model ONCE and cache it"""
    print("Loading sentiment model (first time only)...")
    model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    print("Model loaded!")
    return model

@st.cache_resource
def load_finbert_model():
    """Load FinBERT model ONCE and cache it"""
    print("Loading FinBERT model (first time only)...")
    model = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    print("FinBERT loaded!")
    return model

@st.cache_data
def load_news_data():
    """Load and process news data ONCE"""
    print("Loading news data (first time only)...")
    news_df = load_data("news.csv")
    news_df = compute_sentiment(news_df)
    print(f"Loaded {len(news_df)} news articles")
    return news_df

def analyze_headline(headline, ticker="TSLA", use_enhanced=True):
    """
    Analyze headline with enhanced 5-tier classification system.
    
    Args:
        headline: The news headline to analyze
        ticker: Stock ticker symbol (default: TSLA)
        use_enhanced: If True, uses FinBERT + relevance checking (default: True)
                     If False, uses old 2-class system
    
    Returns:
        dict with keys:
            - category: 'STRONG_POSITIVE', 'POSITIVE', 'NEUTRAL', 'NEGATIVE', 'STRONG_NEGATIVE'
            - polarity: -1.0 to 1.0 (for backward compatibility)
            - impact: Human-readable impact message
            - confidence: 0.0 to 1.0
            - relevance_score: 0.0 to 1.0
            - is_relevant: bool
            - reason: Explanation of classification
            - matched: DataFrame of similar historical headlines
    """
    
    news_df = load_news_data()
    
    if use_enhanced:
        sentiment_result = compute_sentiment_enhanced(headline, ticker, use_finbert=True)
        
        category = sentiment_result['label']
        polarity = sentiment_result['polarity']
        confidence = sentiment_result['confidence']
        relevance_score = sentiment_result['relevance_score']
        is_relevant = sentiment_result['is_relevant']
        reason = sentiment_result['reason']
        
        impact_messages = {
            'STRONG_POSITIVE': f"Strong Positive ({confidence:.2f} confidence) - Significant price increase likely",
            'POSITIVE': f"Positive ({confidence:.2f} confidence) - Price likely to go up",
            'NEUTRAL': f"Neutral/Minimal Impact ({confidence:.2f} confidence) - No significant market impact expected",
            'NEGATIVE': f"Negative ({confidence:.2f} confidence) - Price likely to go down",
            'STRONG_NEGATIVE': f"Strong Negative ({confidence:.2f} confidence) - Significant price decrease likely"
        }
        
        impact = impact_messages.get(category, "Unknown impact")
        
        if not is_relevant:
            impact = f"Neutral - News not directly relevant to {ticker}"
        
    else:
        sentiment_model = load_sentiment_model()
        result = sentiment_model(headline, truncation=True, max_length=512)[0]
        label = result['label']
        score = result['score']
        
        if label == "POSITIVE":
            impact = f"Positive ({score:.2f} confidence) - Price likely to go up"
            polarity = score
            category = 'POSITIVE'
        else:
            impact = f"Negative ({score:.2f} confidence) - Price likely to go down"
            polarity = -score
            category = 'NEGATIVE'
        
        confidence = score
        relevance_score = 1.0
        is_relevant = True
        reason = "Using legacy 2-class sentiment analysis"
    
    matched = compute_similarity(news_df, headline)
    
    return {
        'category': category,
        'polarity': polarity,
        'impact': impact,
        'confidence': confidence,
        'relevance_score': relevance_score,
        'is_relevant': is_relevant,
        'reason': reason,
        'matched': matched[['Date', 'Headline', 'sentiment', 'similarity']].head(3)
    }

def analyze_headline_legacy(headline):
    """
    OLD FUNCTION - Kept for backward compatibility.
    Uses 2-class sentiment only (no neutral detection).
    
    This is what your app.py originally called.
    Now redirects to new system but maintains same return format.
    """
    result = analyze_headline(headline, ticker="TSLA", use_enhanced=False)
    
    return {
        'polarity': result['polarity'],
        'impact': result['impact'],
        'matched': result['matched']
    }
