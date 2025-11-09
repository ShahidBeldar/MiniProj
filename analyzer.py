from transformers import pipeline
from utils import load_data, compute_similarity, compute_sentiment
from functools import lru_cache
import pandas as pd

# ============================================
# CRITICAL: Load models ONCE at module level
# ============================================
print("Loading sentiment model...")
sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("Model loaded successfully!")

# Cache the news data loading
@lru_cache(maxsize=1)
def get_news_data():
    """Load and preprocess news data once, cache the result"""
    print("Loading news data...")
    news_df = load_data("news.csv")
    news_df = compute_sentiment(news_df)
    print(f"Loaded {len(news_df)} news articles")
    return news_df

def analyze_headline(headline):
    """
    Analyze a single headline for sentiment and find similar historical headlines.
    
    Optimizations:
    - Model loaded once at module level (not per request)
    - News data cached with @lru_cache
    - Reduced dataframe operations
    """
    # Run sentiment analysis (fast with pre-loaded model)
    result = sentiment_model(headline, truncation=True, max_length=512)[0]
    label = result['label']
    score = result['score']

    # Convert to polarity & impact message
    if label == "POSITIVE":
        impact = f"✓ Positive ({score:.2f} confidence) - Price likely to go up"
        polarity = score
    else:
        impact = f"✗ Negative ({score:.2f} confidence) - Price likely to go down"
        polarity = -score

    # Get cached news data (loaded once, reused for all requests)
    news_df = get_news_data()
    
    # Compute similarity with historical headlines
    matched = compute_similarity(news_df, headline)

    return {
        'polarity': polarity,
        'impact': impact,
        'matched': matched[['Date', 'Headline', 'sentiment', 'similarity']].head(3).to_dict('records')
    }

# Optional: Clear cache function if needed for updates
def refresh_news_data():
    """Call this function when news.csv is updated"""
    get_news_data.cache_clear()
    return get_news_data()