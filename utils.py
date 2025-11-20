import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import yfinance as yf
import re

# SENTIMENT MODEL - FinBERT Only (Financial-specific)

@st.cache_resource
def get_finbert_model():
    """Load FinBERT model - specialized for financial sentiment analysis"""
    try:
        return pipeline("sentiment-analysis", model="ProsusAI/finbert")
    except Exception as e:
        st.error(f"Failed to load FinBERT model: {e}")
        return None

# TICKER VALIDATION AND CORRECTION

def validate_and_correct_ticker(ticker):
    """
    Validate ticker and add appropriate suffix for international markets.
    Returns: (corrected_ticker, market_name)
    """
    if not ticker or not isinstance(ticker, str):
        return None, None
    
    ticker = ticker.strip().upper()
    
    # If ticker already has suffix, return as is
    if '.' in ticker:
        return ticker, "International"
    
    # Indian NSE stocks - common ones
    indian_stocks = {
        'RELIANCE': 'RELIANCE.NS',
        'TCS': 'TCS.NS',
        'INFY': 'INFY.NS',
        'HDFCBANK': 'HDFCBANK.NS',
        'ICICIBANK': 'ICICIBANK.NS',
        'SBIN': 'SBIN.NS',
        'BHARTIARTL': 'BHARTIARTL.NS',
        'ADANIENT': 'ADANIENT.NS',
        'ADANIPORTS': 'ADANIPORTS.NS',
        'ASIANPAINT': 'ASIANPAINT.NS',
        'AXISBANK': 'AXISBANK.NS',
        'BAJAJ-AUTO': 'BAJAJ-AUTO.NS',
        'BAJFINANCE': 'BAJFINANCE.NS',
        'BAJAJFINSV': 'BAJAJFINSV.NS',
        'BRITANNIA': 'BRITANNIA.NS',
        'CIPLA': 'CIPLA.NS',
        'COALINDIA': 'COALINDIA.NS',
        'DIVISLAB': 'DIVISLAB.NS',
        'DRREDDY': 'DRREDDY.NS',
        'EICHERMOT': 'EICHERMOT.NS',
        'GRASIM': 'GRASIM.NS',
        'HCLTECH': 'HCLTECH.NS',
        'HEROMOTOCO': 'HEROMOTOCO.NS',
        'HINDALCO': 'HINDALCO.NS',
        'HINDUNILVR': 'HINDUNILVR.NS',
        'ITC': 'ITC.NS',
        'INDUSINDBK': 'INDUSINDBK.NS',
        'JSWSTEEL': 'JSWSTEEL.NS',
        'KOTAKBANK': 'KOTAKBANK.NS',
        'LT': 'LT.NS',
        'M&M': 'M&M.NS',
        'MARUTI': 'MARUTI.NS',
        'NESTLEIND': 'NESTLEIND.NS',
        'NTPC': 'NTPC.NS',
        'ONGC': 'ONGC.NS',
        'POWERGRID': 'POWERGRID.NS',
        'SUNPHARMA': 'SUNPHARMA.NS',
        'TATAMOTORS': 'TATAMOTORS.NS',
        'TATASTEEL': 'TATASTEEL.NS',
        'TECHM': 'TECHM.NS',
        'TITAN': 'TITAN.NS',
        'ULTRACEMCO': 'ULTRACEMCO.NS',
        'UPL': 'UPL.NS',
        'WIPRO': 'WIPRO.NS'
    }
    
    # Check if it's a known Indian stock
    if ticker in indian_stocks:
        return indian_stocks[ticker], "NSE (India)"
    
    # US stocks - return as is (most common case)
    # Yahoo Finance handles these without suffix
    return ticker, "US/International"

# RELEVANCE CHECKING

def check_relevance(headline, ticker):
    """
    Check if headline is relevant to the given ticker.
    Returns: (is_relevant: bool, relevance_score: float, reason: str)
    """
    if not headline or not ticker:
        return False, 0.0, "Missing headline or ticker"
    
    try:
        headline_lower = headline.lower()
        
        # Remove market suffix for matching
        ticker_base = ticker.split('.')[0] if '.' in ticker else ticker
        ticker_lower = ticker_base.lower()
        
        # Financial keywords that indicate market relevance
        financial_keywords = [
            'stock', 'shares', 'market', 'trading', 'earnings', 'revenue', 'profit',
            'loss', 'sec', 'sebi', 'fda', 'investor', 'dividend', 'buyback', 'merger',
            'acquisition', 'ipo', 'quarter', 'quarterly', 'annual', 'forecast',
            'guidance', 'analyst', 'rating', 'upgrade', 'downgrade', 'price target',
            'recall', 'lawsuit', 'investigation', 'regulatory', 'compliance',
            'ceo', 'cfo', 'executive', 'board', 'shareholder', 'sales', 'growth',
            'decline', 'bankruptcy', 'debt', 'credit', 'bond', 'valuation',
            'ebitda', 'pe ratio', 'market cap', 'stock split'
        ]
        
        # Expanded company name mapping
        ticker_to_company = {
            # US stocks
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
            # Indian stocks
            'reliance': 'reliance',
            'tcs': 'tata consultancy',
            'infy': 'infosys',
            'hdfcbank': 'hdfc bank',
            'icicibank': 'icici bank',
            'sbin': 'state bank',
            'bhartiartl': 'bharti airtel',
            'adanient': 'adani enterprises',
            'adaniports': 'adani ports',
            'wipro': 'wipro',
            'hindunilvr': 'hindustan unilever',
            'itc': 'itc limited',
            'maruti': 'maruti suzuki',
            'tatamotors': 'tata motors',
            'tatasteel': 'tata steel',
        }
        
        company_name = ticker_to_company.get(ticker_lower, ticker_lower)
        
        # Check 1: Direct ticker or company mention
        ticker_mentioned = ticker_lower in headline_lower or company_name in headline_lower
        
        # Check 2: Financial keywords present
        financial_keyword_count = sum(1 for keyword in financial_keywords if keyword in headline_lower)
        
        # Check 3: Industry-specific terms
        industry_keywords = [
            'tech', 'technology', 'automotive', 'electric vehicle', 'ev', 
            'software', 'hardware', 'pharmaceutical', 'banking', 'finance',
            'telecom', 'energy', 'steel', 'cement', 'fmcg'
        ]
        industry_mentioned = any(keyword in headline_lower for keyword in industry_keywords)
        
        # Calculate relevance score
        score = 0.0
        reasons = []
        
        if ticker_mentioned:
            score += 0.6
            reasons.append("Ticker or company mentioned")
        
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
            'recipe', 'fashion', 'celebrity', 'gossip', 'wedding', 'party'
        ]
        
        irrelevant_count = sum(1 for keyword in irrelevant_keywords if keyword in headline_lower)
        if irrelevant_count > 0:
            score -= 0.3
            reasons.append("Irrelevant keywords detected")
        
        # Final determination
        score = max(0.0, min(1.0, score))
        is_relevant = score >= 0.4
        
        reason = "; ".join(reasons) if reasons else "No clear relevance indicators"
        
        return is_relevant, score, reason
    
    except Exception as e:
        return False, 0.0, f"Error checking relevance: {str(e)}"

# DATA LOADING

def load_data(filepath):
    """
    Load CSV data and automatically detect the headline column.
    """
    try:
        df = pd.read_csv(filepath)
        
        if df.empty:
            raise ValueError(f"CSV file {filepath} is empty")
        
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
    
    except FileNotFoundError:
        st.error(f"File not found: {filepath}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data from {filepath}: {str(e)}")
        return pd.DataFrame()

def get_stock_data(ticker, period="1y"):
    """
    Fetch stock data using yfinance with comprehensive safety checks.
    Automatically handles Indian stocks by adding .NS suffix.
    """
    try:
        if not ticker or not isinstance(ticker, str):
            st.error("Invalid ticker symbol provided")
            return None
        
        # Validate and correct ticker
        corrected_ticker, market = validate_and_correct_ticker(ticker)
        
        if not corrected_ticker:
            st.error(f"Invalid ticker: {ticker}")
            return None
        
        # Show market info if ticker was corrected
        if corrected_ticker != ticker:
            st.info(f"Using {corrected_ticker} for {market} market")
        
        stock = yf.Ticker(corrected_ticker)
        df = stock.history(period=period)
        
        if df is None or df.empty:
            st.warning(f"No stock data available for {corrected_ticker}. Please verify the ticker symbol.")
            
            # Suggest alternative for Indian stocks
            if market == "US/International" and not '.' in ticker:
                st.info(f"Tip: For Indian stocks, try adding .NS (NSE) or .BO (BSE) suffix. Example: {ticker}.NS")
            
            return None
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Ensure Date column exists
        if 'Date' not in df.columns:
            date_column_candidates = ['Datetime', 'Timestamp', 'index', 'date']
            date_col_found = None
            
            for col_name in date_column_candidates:
                if col_name in df.columns:
                    date_col_found = col_name
                    break
            
            if date_col_found:
                df = df.rename(columns={date_col_found: 'Date'})
                print(f"Renamed '{date_col_found}' to 'Date'")
            else:
                print("WARNING: No date column found, creating synthetic dates")
                df.insert(0, 'Date', pd.date_range(
                    end=pd.Timestamp.now(), 
                    periods=len(df), 
                    freq='D'
                ))
        
        # Ensure Date is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df['Date']):
            try:
                df['Date'] = pd.to_datetime(df['Date'])
            except Exception as e:
                print(f"Warning: Could not convert Date to datetime: {e}")
        
        # Validate required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            return None
        
        # Remove any rows with NaN in critical columns
        df = df.dropna(subset=['Close', 'Date'])
        
        if df.empty:
            st.warning(f"All data rows were invalid for {corrected_ticker}")
            return None
        
        print(f"Successfully fetched {len(df)} rows of stock data for {corrected_ticker}")
        return df
    
    except Exception as e:
        st.error(f"Error fetching stock data for {ticker}: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

# ENHANCED SENTIMENT COMPUTATION - FinBERT Only

def compute_sentiment_enhanced(headline, ticker, use_finbert=True):
    """
    Financial sentiment analysis using FinBERT with relevance checking.
    
    Returns dict with:
        - label: 'STRONG_POSITIVE', 'POSITIVE', 'NEUTRAL', 'NEGATIVE', 'STRONG_NEGATIVE'
        - polarity: -1.0 to 1.0
        - confidence: 0.0 to 1.0
        - relevance_score: 0.0 to 1.0
        - is_relevant: bool
        - reason: explanation string
    """
    
    if not headline or not isinstance(headline, str):
        return {
            'label': 'NEUTRAL',
            'polarity': 0.0,
            'confidence': 0.0,
            'relevance_score': 0.0,
            'is_relevant': False,
            'reason': 'Invalid or empty headline',
            'raw_sentiment': 'NEUTRAL'
        }
    
    try:
        # Step 1: Check relevance
        is_relevant, relevance_score, relevance_reason = check_relevance(headline, ticker)
        
        # Step 2: Get sentiment using FinBERT
        model = get_finbert_model()
        if model is None:
            return {
                'label': 'NEUTRAL',
                'polarity': 0.0,
                'confidence': 0.0,
                'relevance_score': relevance_score,
                'is_relevant': is_relevant,
                'reason': 'FinBERT model not available',
                'raw_sentiment': 'ERROR'
            }
        
        result = model(headline, truncation=True, max_length=512)[0]
        
        sentiment_label = result['label'].upper()
        confidence = result['score']
        
        # Map FinBERT labels to polarity
        if sentiment_label == 'POSITIVE':
            polarity = confidence
        elif sentiment_label == 'NEGATIVE':
            polarity = -confidence
        else:  # NEUTRAL
            polarity = 0.0
        
        # Step 3: Adjust based on relevance and confidence
        if not is_relevant:
            final_label = 'NEUTRAL'
            final_polarity = 0.0
            ticker_base = ticker.split('.')[0] if '.' in ticker else ticker
            reason = f"News not relevant to {ticker_base}. {relevance_reason}"
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
                reason = "Neutral sentiment detected by FinBERT"
        
        return {
            'label': final_label,
            'polarity': final_polarity,
            'confidence': confidence,
            'relevance_score': relevance_score,
            'is_relevant': is_relevant,
            'reason': reason,
            'raw_sentiment': sentiment_label
        }
    
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return {
            'label': 'NEUTRAL',
            'polarity': 0.0,
            'confidence': 0.0,
            'relevance_score': 0.0,
            'is_relevant': False,
            'reason': f'Error during analysis: {str(e)}',
            'raw_sentiment': 'ERROR'
        }

# LEGACY FUNCTION (for backward compatibility with existing news.csv)

def compute_sentiment(df):
    """
    Add sentiment scores to dataframe with BATCH PROCESSING using FinBERT.
    """
    try:
        if df is None or df.empty:
            return df
        
        if 'sentiment' in df.columns:
            return df
        
        if 'Headline' not in df.columns:
            raise KeyError(f"'Headline' column not found. Available: {df.columns.tolist()}")
        
        sentiment_model = get_finbert_model()
        if sentiment_model is None:
            st.warning("FinBERT model not available, skipping sentiment computation")
            df['sentiment'] = 0.0
            return df
        
        headlines = df['Headline'].fillna("").tolist()
        headlines = [h if h.strip() else "neutral news" for h in headlines]
        
        batch_size = 16  # Smaller batch for FinBERT
        sentiments = []
        
        for i in range(0, len(headlines), batch_size):
            batch = headlines[i:i + batch_size]
            
            try:
                results = sentiment_model(batch, truncation=True, max_length=512)
                
                for result in results:
                    label = result['label'].upper()
                    score = result['score']
                    
                    if label == 'POSITIVE':
                        sentiments.append(score)
                    elif label == 'NEGATIVE':
                        sentiments.append(-score)
                    else:  # NEUTRAL
                        sentiments.append(0.0)
            except Exception as e:
                print(f"Error processing batch: {e}")
                sentiments.extend([0.0] * len(batch))
        
        df['sentiment'] = sentiments
        return df
    
    except Exception as e:
        print(f"Error in compute_sentiment: {e}")
        if df is not None and not df.empty:
            df['sentiment'] = 0.0
        return df

# SIMILARITY COMPUTATION

def compute_similarity(news_df, headline, top_n=10):
    """
    Find most similar historical headlines using TF-IDF.
    """
    try:
        if news_df is None or news_df.empty:
            return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])
        
        if 'Headline' not in news_df.columns:
            raise KeyError(f"'Headline' column not found. Available: {news_df.columns.tolist()}")
        
        if not headline or not isinstance(headline, str):
            return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])
        
        all_headlines = news_df['Headline'].fillna("").tolist() + [headline]
        
        # Filter out empty strings
        valid_headlines = [h for h in all_headlines if h.strip()]
        
        if len(valid_headlines) < 2:
            return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])
        
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        
        tfidf_matrix = vectorizer.fit_transform(all_headlines)
        query_vector = tfidf_matrix[-1]
        similarity_scores = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
        
        result_df = news_df.copy()
        result_df['similarity'] = similarity_scores
        
        # Ensure required columns exist
        for col in ['Date', 'sentiment']:
            if col not in result_df.columns:
                result_df[col] = 'N/A' if col == 'Date' else 0.0
        
        return result_df.nlargest(top_n, 'similarity')
    
    except Exception as e:
        print(f"Error computing similarity: {e}")
        return pd.DataFrame(columns=['Date', 'Headline', 'sentiment', 'similarity'])
