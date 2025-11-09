import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import numpy as np

# Load sentiment model once at module level
sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def load_data(filepath):
    """Load CSV data efficiently"""
    return pd.read_csv(filepath)

def compute_sentiment(df):
    """
    Add sentiment scores to dataframe.
    Optimized with batch processing.
    """
    if 'sentiment' in df.columns:
        return df  # Already computed
    
    # Batch processing for faster inference (process 32 at a time)
    headlines = df['Headline'].fillna("").tolist()
    
    # Process in batches of 32 (much faster than one-by-one)
    batch_size = 32
    sentiments = []
    
    for i in range(0, len(headlines), batch_size):
        batch = headlines[i:i + batch_size]
        results = sentiment_model(batch, truncation=True, max_length=512)
        
        for result in results:
            if result['label'] == 'POSITIVE':
                sentiments.append(result['score'])
            else:
                sentiments.append(-result['score'])
    
    df['sentiment'] = sentiments
    return df

def compute_similarity(news_df, headline, top_n=10):
    """
    Find most similar historical headlines using TF-IDF + cosine similarity.
    Optimized to return only top N results.
    """
    # Combine all headlines with the query
    all_headlines = news_df['Headline'].fillna("").tolist() + [headline]
    
    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=5000,  # Limit features for speed
        stop_words='english',
        ngram_range=(1, 2)  # Unigrams and bigrams
    )
    
    tfidf_matrix = vectorizer.fit_transform(all_headlines)
    
    # Compute similarity between query and all headlines
    query_vector = tfidf_matrix[-1]
    similarity_scores = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
    
    # Add similarity scores to dataframe
    result_df = news_df.copy()
    result_df['similarity'] = similarity_scores
    
    # Return only top N most similar (sorted)
    return result_df.nlargest(top_n, 'similarity')


# ============================================
# ALTERNATIVE: Even Faster with Pre-computed Embeddings
# ============================================
# If you want MAXIMUM speed, pre-compute TF-IDF vectors at startup:

class FastSimilarityMatcher:
    """Pre-compute TF-IDF for ultra-fast similarity search"""
    
    def __init__(self, news_df):
        self.news_df = news_df
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Pre-compute TF-IDF matrix for all historical headlines
        headlines = news_df['Headline'].fillna("").tolist()
        self.tfidf_matrix = self.vectorizer.fit_transform(headlines)
        print(f"Pre-computed TF-IDF for {len(headlines)} headlines")
    
    def find_similar(self, headline, top_n=10):
        """Find similar headlines in <100ms"""
        # Transform query headline
        query_vector = self.vectorizer.transform([headline])
        
        # Compute similarity
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get top N indices
        top_indices = np.argsort(similarity_scores)[-top_n:][::-1]
        
        # Create result dataframe
        result_df = self.news_df.iloc[top_indices].copy()
        result_df['similarity'] = similarity_scores[top_indices]
        
        return result_df

# Usage in analyser.py:
# from utils import FastSimilarityMatcher
# matcher = FastSimilarityMatcher(get_news_data())  # Initialize once
# matched = matcher.find_similar(headline)  # Ultra-fast lookups