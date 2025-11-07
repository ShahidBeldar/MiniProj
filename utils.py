import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import yfinance as yf

# Load HuggingFace sentiment model once (cached for reuse)
sentiment_model = pipeline("sentiment-analysis")

def load_data(path):
    df = pd.read_csv(path)
    # Handle both "Headline" and "Top1" column names
    if "Top1" in df.columns:
        df.rename(columns={'Top1': 'Headline'}, inplace=True)
    df['Headline'] = df['Headline'].astype(str)
    df.dropna(subset=['Headline'], inplace=True)
    return df

def compute_sentiment(df):
    """
    Apply transformer sentiment analysis to the dataset headlines.
    Adds 'sentiment' column with polarity score.
    """
    sentiments = []
    for text in df['Headline']:
        try:
            result = sentiment_model(text)[0]
            if result['label'] == "POSITIVE":
                score = result['score']
            else:
                score = -result['score']
            sentiments.append(score)
        except Exception:
            sentiments.append(0.0)  # fallback if error
    df['sentiment'] = sentiments
    return df

def compute_similarity(df, fake_headline):
    headlines = df['Headline'].tolist()
    all_text = headlines + [fake_headline]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_text)

    sim_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    df['similarity'] = sim_scores[0]
    return df.sort_values(by='similarity', ascending=False)

def get_stock_data(ticker="TSLA", period="6mo"):
    """
    Fetch historical stock data using yfinance.
    Example tickers:
      TSLA -> Tesla
      AAPL -> Apple
      INFY.NS -> Infosys (NSE India)
      RELIANCE.NS -> Reliance Industries (NSE India)
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None
