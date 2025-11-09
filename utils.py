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
# DATA LOADING
# ============================================

def load_data(filepath):
    """Load CSV data"""
    return pd.read_csv(filepath)

def get_stock_data(ticker, period="1y"):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
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
    
    sentiment_model = get_sentiment_model()
    
    # Prepare headlines
    headlines = df['Headline'].fillna("").tolist()
    
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
            print(f"Error processing batch: {e}")
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
        print(f"Error computing similarity: {e}")
        # Return empty dataframe with required columns
        return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])


# ============================================
# OPTIONAL: Ultra-Fast Version (if you want <1s responses)
# ============================================
# Uncomment this section if you want even faster performance

"""
class FastSimilarityMatcher:
    '''Pre-compute TF-IDF vectors for instant similarity search'''
    
    def __init__(self, news_df):
        self.news_df = news_df.copy()
        headlines = news_df['Headline'].fillna("").tolist()
        
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(headlines)
        print(f"✅ Pre-computed TF-IDF for {len(headlines)} headlines")
    
    def find_similar(self, headline, top_n=10):
        '''Find similar headlines in <100ms'''
        try:
            query_vector = self.vectorizer.transform([headline])
            similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            top_indices = similarity_scores.argsort()[-top_n:][::-1]
            
            result_df = self.news_df.iloc[top_indices].copy()
            result_df['similarity'] = similarity_scores[top_indices]
            
            return result_df
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])

# To use FastSimilarityMatcher in analyzer.py:
# 1. Import: from utils import FastSimilarityMatcher
# 2. In analyzer.py, create cached matcher:
#    @st.cache_resource
#    def get_matcher(_news_df):
#        return FastSimilarityMatcher(_news_df)
# 3. Use: matched = matcher.find_similar(headline)
"""