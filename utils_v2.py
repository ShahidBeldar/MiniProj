import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import yfinance as yf
import re

# SENTIMENT MODELS (Cached)

@st.cache_resource
def get_sentiment_model():
    """Load old sentiment model (2-class) - kept for fallback"""
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

@st.cache_resource
def get_finbert_model():
    """Load FinBERT model (3-class with NEUTRAL support)"""
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

# RELEVANCE CHECKING

def check_relevance(headline, ticker):
    """
    Check if headline is relevant to the given ticker.
    Returns: (is_relevant: bool, relevance_score: float, reason: str)
    """
    headline_lower = headline.lower()
    ticker_lower = ticker.lower()
    
    # Financial keywords that indicate market relevance
    financial_keywords = [
        'stock', 'shares', 'market', 'trading', 'earnings', 'revenue', 'profit',
        'loss', 'sec', 'fda', 'investor', 'dividend', 'buyback', 'merger',
        'acquisition', 'ipo', 'quarter', 'quarterly', 'annual', 'forecast',
        'guidance', 'analyst', 'rating', 'upgrade', 'downgrade', 'price target',
        'recall', 'lawsuit', 'investigation', 'regulatory', 'compliance',
        'ceo', 'executive', 'board', 'shareholder', 'sales', 'growth',
        'decline', 'bankruptcy', 'debt', 'credit', 'bond', 'valuation'
    ]
    
    # Company name mapping (extend this as needed)
    ticker_to_company = {
        'aapl': 'apple',
        'tsla': 'tesla',
        'msft': 'microsoft',
        'googl': 'google',
        'goog': 'google',
        'amzn': 'amazon',
        'meta': 'meta',
        'fb': 'facebook',
        'nflx': 'netflix',
        'nvda': 'nvidia',
        'amd': 'amd',
        'intc': 'intel',
    }
    
    company_name = ticker_to_company.get(ticker_lower, ticker_lower)
    
    # Check 1: Direct ticker or company mention
    ticker_mentioned = ticker_lower in headline_lower or company_name in headline_lower
    
    # Check 2: Financial keywords present
    financial_keyword_count = sum(1 for keyword in financial_keywords if keyword in headline_lower)
    
    # Check 3: Industry-specific terms (can be extended)
    industry_keywords = ['tech', 'technology', 'automotive', 'electric vehicle', 'ev', 'software', 'hardware']
    industry_mentioned = any(keyword in headline_lower for keyword in industry_keywords)
    
    # Calculate relevance score
    score = 0.0
    reasons = []
    
    if ticker_mentioned:
        score += 0.6
        reasons.append(f"Ticker/company mentioned")
    
    if financial_keyword_count > 0:
        score += min(0.3, financial_keyword_count * 0.1)
        reasons.append(f"{financial_keyword_count} financial keywords found")
    
    if industry_mentioned and ticker_mentioned:
        score += 0.1
        reasons.append("Industry context present")
    
    # Negative signals (entertainment, sports, weather)
    irrelevant_keywords = [
        'concert', 'tour', 'album', 'movie', 'film', 'actor', 'actress',
        'sports', 'game', 'match', 'weather', 'forecast', 'restaurant',
        'recipe', 'fashion', 'celebrity', 'gossip'
    ]
    
    irrelevant_count = sum(1 for keyword in irrelevant_keywords if keyword in headline_lower)
    if irrelevant_count > 0:
        score -= 0.3
        reasons.append(f"Irrelevant keywords detected")
    
    # Final determination
    score = max(0.0, min(1.0, score))
    is_relevant = score >= 0.4
    
    reason = "; ".join(reasons) if reasons else "No clear relevance indicators"
    
    return is_relevant, score, reason

# DATA LOADING

def load_data(filepath):
    """
    Load CSV data and automatically detect the headline column.
    """
    df = pd.read_csv(filepath)
    
    print(f"CSV columns found: {df.columns.tolist()}")
    
    possible_headline_cols = [
        'Headline', 'headline', 'HEADLINE',
        'Title', 'title', 'TITLE',
        'News', 'news', 'NEWS',
        'Text', 'text', 'TEXT',
        'Description', 'description', 'DESCRIPTION',
        'Article', 'article'
    ]
    
    headline_col = None
    for col in possible_headline_cols:
        if col in df.columns:
            headline_col = col
            break
    
    if headline_col:
        if headline_col != 'Headline':
            df = df.rename(columns={headline_col: 'Headline'})
        print(f"Using column '{headline_col}' as Headline")
    else:
        text_columns = df.select_dtypes(include=['object']).columns
        if len(text_columns) > 0:
            df = df.rename(columns={text_columns[0]: 'Headline'})
            print(f"No standard headline column found. Using '{text_columns[0]}'")
        else:
            raise KeyError(
                f"Could not find a headline column! Available columns: {df.columns.tolist()}"
            )
    
    possible_date_cols = ['Date', 'date', 'DATE', 'Time', 'time', 'Timestamp', 'timestamp', 'Published', 'published']
    date_col = None
    for col in possible_date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if date_col and date_col != 'Date':
        df = df.rename(columns={date_col: 'Date'})
        print(f"Using column '{date_col}' as Date")
    elif 'Date' not in df.columns:
        df['Date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        print("No date column found. Added placeholder dates.")
    
    return df

def get_stock_data(ticker, period="1y"):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df is not None and not df.empty:
            df = df.reset_index()
            print(f"Fetched {len(df)} rows of stock data for {ticker}")
        
        return df
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return None

# ENHANCED SENTIMENT COMPUTATION

def compute_sentiment_enhanced(headline, ticker, use_finbert=True):
    """
    Enhanced sentiment analysis with relevance checking and neutral support.
    
    Returns dict with:
        - label: 'STRONG_POSITIVE', 'POSITIVE', 'NEUTRAL', 'NEGATIVE', 'STRONG_NEGATIVE'
        - polarity: -1.0 to 1.0
        - confidence: 0.0 to 1.0
        - relevance_score: 0.0 to 1.0
        - is_relevant: bool
        - reason: explanation string
    """
    
    # Step 1: Check relevance
    is_relevant, relevance_score, relevance_reason = check_relevance(headline, ticker)
    
    # Step 2: Get sentiment
    if use_finbert:
        try:
            model = get_finbert_model()
            result = model(headline, truncation=True, max_length=512)[0]
            
            sentiment_label = result['label'].upper()
            confidence = result['score']
            
            # Map FinBERT labels to our system
            if sentiment_label == 'POSITIVE':
                polarity = confidence
            elif sentiment_label == 'NEGATIVE':
                polarity = -confidence
            else:
                polarity = 0.0
            
        except Exception as e:
            print(f"FinBERT failed, falling back to old model: {e}")
            model = get_sentiment_model()
            result = model(headline, truncation=True, max_length=512)[0]
            confidence = result['score']
            
            if result['label'] == 'POSITIVE':
                polarity = confidence
                sentiment_label = 'POSITIVE'
            else:
                polarity = -confidence
                sentiment_label = 'NEGATIVE'
    else:
        model = get_sentiment_model()
        result = model(headline, truncation=True, max_length=512)[0]
        confidence = result['score']
        
        if result['label'] == 'POSITIVE':
            polarity = confidence
            sentiment_label = 'POSITIVE'
        else:
            polarity = -confidence
            sentiment_label = 'NEGATIVE'
    
    # Step 3: Adjust based on relevance and confidence
    if not is_relevant:
        final_label = 'NEUTRAL'
        final_polarity = 0.0
        reason = f"News not relevant to {ticker}. {relevance_reason}"
    elif confidence < 0.6:
        final_label = 'NEUTRAL'
        final_polarity = 0.0
        reason = f"Low confidence ({confidence:.2f}). Insufficient signal for prediction."
    else:
        # Strong vs regular classification
        if sentiment_label == 'POSITIVE':
            if confidence >= 0.85 and relevance_score >= 0.7:
                final_label = 'STRONG_POSITIVE'
            else:
                final_label = 'POSITIVE'
            final_polarity = polarity
            reason = f"Positive sentiment detected with {confidence:.2f} confidence"
        elif sentiment_label == 'NEGATIVE':
            if confidence >= 0.85 and relevance_score >= 0.7:
                final_label = 'STRONG_NEGATIVE'
            else:
                final_label = 'NEGATIVE'
            final_polarity = polarity
            reason = f"Negative sentiment detected with {confidence:.2f} confidence"
        else:
            final_label = 'NEUTRAL'
            final_polarity = 0.0
            reason = "Neutral sentiment detected"
    
    return {
        'label': final_label,
        'polarity': final_polarity,
        'confidence': confidence,
        'relevance_score': relevance_score,
        'is_relevant': is_relevant,
        'reason': reason,
        'raw_sentiment': sentiment_label
    }

# LEGACY FUNCTION (for backward compatibility with existing news.csv)

def compute_sentiment(df):
    """
    Add sentiment scores to dataframe with BATCH PROCESSING.
    This is the old function - kept for loading historical data.
    """
    if 'sentiment' in df.columns:
        return df
    
    if 'Headline' not in df.columns:
        raise KeyError(f"'Headline' column not found. Available: {df.columns.tolist()}")
    
    sentiment_model = get_sentiment_model()
    
    headlines = df['Headline'].fillna("").tolist()
    headlines = [h if h.strip() else "neutral news" for h in headlines]
    
    batch_size = 32
    sentiments = []
    
    for i in range(0, len(headlines), batch_size):
        batch = headlines[i:i + batch_size]
        
        try:
            results = sentiment_model(batch, truncation=True, max_length=512)
            
            for result in results:
                if result['label'] == 'POSITIVE':
                    sentiments.append(result['score'])
                else:
                    sentiments.append(-result['score'])
        except Exception as e:
            print(f"Error processing batch: {e}")
            sentiments.extend([0.0] * len(batch))
    
    df['sentiment'] = sentiments
    return df

# SIMILARITY COMPUTATION

def compute_similarity(news_df, headline, top_n=10):
    """
    Find most similar historical headlines using TF-IDF.
    """
    if 'Headline' not in news_df.columns:
        raise KeyError(f"'Headline' column not found. Available: {news_df.columns.tolist()}")
    
    all_headlines = news_df['Headline'].fillna("").tolist() + [headline]
    
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_headlines)
        query_vector = tfidf_matrix[-1]
        similarity_scores = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
        
        result_df = news_df.copy()
        result_df['similarity'] = similarity_scores
        
        return result_df.nlargest(top_n, 'similarity')
    
    except Exception as e:
        print(f"Error computing similarity: {e}")
        return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])
