import streamlit as st
from transformers import pipeline
from utils import (
    load_data, 
    compute_similarity, 
    compute_sentiment, 
    compute_sentiment_enhanced,
    preprocess_headline
)

# Cache the FinBERT model

@st.cache_resource
def load_finbert_model():
    """Load FinBERT model ONCE and cache it"""
    print("Loading FinBERT model (first time only)...")
    try:
        model = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        print("FinBERT loaded successfully!")
        return model
    except Exception as e:
        print(f"Error loading FinBERT: {e}")
        return None

@st.cache_data
def load_news_data():
    """Load and process news data ONCE"""
    print("Loading news data (first time only)...")
    try:
        news_df = load_data("news.csv")
        if news_df is not None and not news_df.empty:
            news_df = compute_sentiment(news_df)
            print(f"Loaded {len(news_df)} news articles")
        else:
            print("Warning: News data is empty or could not be loaded")
            news_df = None
        return news_df
    except Exception as e:
        print(f"Error loading news data: {e}")
        return None

def analyze_headline(headline, ticker="TSLA", use_enhanced=True):
    """
    Analyze headline with enhanced 5-tier classification system using FinBERT.
    Now includes all safety features: preprocessing, jargon detection, multi-company detection.
    
    Args:
        headline: The news headline to analyze
        ticker: Stock ticker symbol (supports US and Indian stocks)
        use_enhanced: Always True (legacy parameter for compatibility)
    
    Returns:
        dict with comprehensive analysis including:
            - category: 5-tier classification
            - polarity: -1.0 to 1.0
            - impact: Human-readable message
            - confidence: 0.0 to 1.0
            - relevance_score: 0.0 to 1.0
            - is_relevant: bool
            - reason: Detailed explanation
            - matched: Similar historical headlines
            - warnings: Any temporal or comparison warnings
            - jargon_detected: Financial terms found
    """
    
    if not headline or not isinstance(headline, str) or not headline.strip():
        return {
            'category': 'NEUTRAL',
            'polarity': 0.0,
            'impact': 'Invalid headline provided',
            'confidence': 0.0,
            'relevance_score': 0.0,
            'is_relevant': False,
            'reason': 'No valid headline to analyze',
            'matched': None,
            'warnings': [],
            'jargon_detected': []
        }
    
    try:
        news_df = load_news_data()
        
        # Always use FinBERT-based enhanced analysis with all features
        sentiment_result = compute_sentiment_enhanced(headline, ticker, use_finbert=True)
        
        category = sentiment_result['label']
        polarity = sentiment_result['polarity']
        confidence = sentiment_result['confidence']
        relevance_score = sentiment_result['relevance_score']
        is_relevant = sentiment_result['is_relevant']
        reason = sentiment_result['reason']
        is_comparison = sentiment_result.get('is_comparison', False)
        temporal_warning = sentiment_result.get('temporal_warning', '')
        jargon_detected = sentiment_result.get('jargon_detected', [])
        
        # Generate impact messages
        ticker_display = ticker.split('.')[0] if '.' in ticker else ticker
        
        impact_messages = {
            'STRONG_POSITIVE': f"Strong Positive ({confidence:.2f} confidence) - Significant price increase likely for {ticker_display}",
            'POSITIVE': f"Positive ({confidence:.2f} confidence) - Price likely to go up for {ticker_display}",
            'NEUTRAL': f"Neutral/Minimal Impact ({confidence:.2f} confidence) - No significant market impact expected for {ticker_display}",
            'NEGATIVE': f"Negative ({confidence:.2f} confidence) - Price likely to go down for {ticker_display}",
            'STRONG_NEGATIVE': f"Strong Negative ({confidence:.2f} confidence) - Significant price decrease likely for {ticker_display}"
        }
        
        impact = impact_messages.get(category, "Unknown impact")
        
        # Add comparison note if detected
        if is_comparison:
            impact = f"{impact} (Comparative analysis from {ticker_display} perspective)"
        
        # Adjust impact if not relevant
        if not is_relevant:
            impact = f"Neutral - News not directly relevant to {ticker_display}"
        
        # Collect warnings
        warnings = []
        if temporal_warning:
            warnings.append(temporal_warning)
        if is_comparison:
            warnings.append("Multi-company comparison detected")
        
        # Find similar historical headlines
        if news_df is not None and not news_df.empty:
            matched = compute_similarity(news_df, headline)
        else:
            import pandas as pd
            matched = pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])
        
        return {
            'category': category,
            'polarity': polarity,
            'impact': impact,
            'confidence': confidence,
            'relevance_score': relevance_score,
            'is_relevant': is_relevant,
            'reason': reason,
            'matched': matched[['Date', 'Headline', 'sentiment', 'similarity']].head(3) if not matched.empty else matched,
            'warnings': warnings,
            'jargon_detected': jargon_detected
        }
    
    except Exception as e:
        print(f"Error in analyze_headline: {e}")
        import traceback
        print(traceback.format_exc())
        
        import pandas as pd
        return {
            'category': 'NEUTRAL',
            'polarity': 0.0,
            'impact': f'Error during analysis: {str(e)}',
            'confidence': 0.0,
            'relevance_score': 0.0,
            'is_relevant': False,
            'reason': f'Analysis failed: {str(e)}',
            'matched': pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity']),
            'warnings': ['Analysis error occurred'],
            'jargon_detected': []
        }

def analyze_headline_legacy(headline):
    """
    DEPRECATED: Old function for backward compatibility.
    Redirects to new FinBERT-based system.
    """
    result = analyze_headline(headline, ticker="TSLA", use_enhanced=True)
    
    return {
        'polarity': result['polarity'],
        'impact': result['impact'],
        'matched': result['matched']
    }
