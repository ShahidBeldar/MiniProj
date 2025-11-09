import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import yfinance as yf

# ============================================
# SENTIMENT MODEL (Cached)
# ============================================

@st.cache_resource
def get_sentiment_model():
    """Load sentiment model once and cache it"""
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# ============================================
# DATA LOADING (Fixed for different column names)
# ============================================

def load_data(filepath):
    """
    Load CSV data and automatically detect the headline column.
    Handles different column names: Headline, headline, title, Title, news, etc.
    """
    df = pd.read_csv(filepath)
    
    print(f"📋 CSV columns found: {df.columns.tolist()}")
    
    # List of possible column names for headlines
    possible_headline_cols = [
        'Headline', 'headline', 'HEADLINE',
        'Title', 'title', 'TITLE',
        'News', 'news', 'NEWS',
        'Text', 'text', 'TEXT',
        'Description', 'description', 'DESCRIPTION',
        'Article', 'article'
    ]
    
    # Find the headline column
    headline_col = None
    for col in possible_headline_cols:
        if col in df.columns:
            headline_col = col
            break
    
    # Rename to 'Headline' for consistency
    if headline_col:
        if headline_col != 'Headline':
            df = df.rename(columns={headline_col: 'Headline'})
        print(f"✅ Using column '{headline_col}' as Headline")
    else:
        # Use first text column as fallback
        text_columns = df.select_dtypes(include=['object']).columns
        if len(text_columns) > 0:
            df = df.rename(columns={text_columns[0]: 'Headline'})
            print(f"⚠️ No standard headline column found. Using '{text_columns[0]}'")
        else:
            raise KeyError(
                f"❌ Could not find a headline column!\n"
                f"Available columns: {df.columns.tolist()}\n"
                f"Please ensure your CSV has a column like 'Headline', 'Title', or 'News'"
            )
    
    # Handle Date column (optional)
    possible_date_cols = ['Date', 'date', 'DATE', 'Time', 'time', 'Timestamp', 'timestamp', 'Published', 'published']
    date_col = None
    for col in possible_date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if date_col and date_col != 'Date':
        df = df.rename(columns={date_col: 'Date'})
        print(f"✅ Using column '{date_col}' as Date")
    elif 'Date' not in df.columns:
        df['Date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        print("⚠️ No date column found. Added placeholder dates.")
    
    return df

def get_stock_data(ticker, period="1y"):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        # FIX: yfinance stores date as index, not as a column
        # Reset index to make 'Date' an actual column
        if df is not None and not df.empty:
            df = df.reset_index()
            print(f"✅ Fetched {len(df)} rows of stock data for {ticker}")
        
        return df
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return None

# ============================================
# SENTIMENT COMPUTATION (Batch Processing)
# ============================================

def compute_sentiment(df):
    """
    Add sentiment scores to dataframe with BATCH PROCESSING.
    This is 10-20x faster than processing one-by-one!
    """
    if 'sentiment' in df.columns:
        return df  # Already computed
    
    # Ensure Headline column exists
    if 'Headline' not in df.columns:
        raise KeyError(f"'Headline' column not found after loading. Available columns: {df.columns.tolist()}")
    
    sentiment_model = get_sentiment_model()
    
    # Prepare headlines
    headlines = df['Headline'].fillna("").tolist()
    
    # Filter out empty headlines
    headlines = [h if h.strip() else "neutral news" for h in headlines]
    
    # BATCH PROCESSING: Process 32 headlines at once (MUCH faster!)
    batch_size = 32
    sentiments = []
    
    for i in range(0, len(headlines), batch_size):
        batch = headlines[i:i + batch_size]
        
        try:
            # Process entire batch at once
            results = sentiment_model(batch, truncation=True, max_length=512)
            
            for result in results:
                if result['label'] == 'POSITIVE':
                    sentiments.append(result['score'])
                else:
                    sentiments.append(-result['score'])
        except Exception as e:
            print(f"⚠️ Error processing batch: {e}")
            # Fill with neutral sentiment if batch fails
            sentiments.extend([0.0] * len(batch))
    
    df['sentiment'] = sentiments
    return df

# ============================================
# SIMILARITY COMPUTATION
# ============================================

def compute_similarity(news_df, headline, top_n=10):
    """
    Find most similar historical headlines using TF-IDF.
    Optimized to return only top N results.
    """
    # Ensure Headline column exists
    if 'Headline' not in news_df.columns:
        raise KeyError(f"'Headline' column not found. Available columns: {news_df.columns.tolist()}")
    
    # Combine all headlines with the query
    all_headlines = news_df['Headline'].fillna("").tolist() + [headline]
    
    # TF-IDF vectorization (optimized parameters)
    vectorizer = TfidfVectorizer(
        max_features=5000,      # Limit features for speed
        stop_words='english',    # Remove common words
        ngram_range=(1, 2),      # Unigrams and bigrams
        min_df=2                 # Ignore rare terms
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_headlines)
        
        # Compute similarity between query and all headlines
        query_vector = tfidf_matrix[-1]
        similarity_scores = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
        
        # Add similarity scores to dataframe
        result_df = news_df.copy()
        result_df['similarity'] = similarity_scores
        
        # Return only top N most similar (sorted descending)
        return result_df.nlargest(top_n, 'similarity')
    
    except Exception as e:
        print(f"❌ Error computing similarity: {e}")
        # Return empty dataframe with required columns
        return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])