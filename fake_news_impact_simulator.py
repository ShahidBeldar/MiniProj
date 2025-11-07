### 📁 Project Structure: fake-news-impact-simulator

# ├── app.py                # Streamlit frontend app
# ├── news.csv             # Dataset of historical news headlines
# ├── tesla_stock.csv      # Historical stock prices from yfinance
# ├── analyzer.py          # Backend logic: sentiment + similarity
# ├── utils.py             # Utility functions for preprocessing
# ├── requirements.txt     # All dependencies
# └── README.md            # How to run project


# ===============================
# 📄 app.py
# ===============================
import streamlit as st
from analyzer import analyze_headline

st.title(" Fake News Impact Simulator")
st.markdown("Enter a fake news headline to simulate its impact on Tesla stock.")

user_input = st.text_area("Enter Fake News Headline")

if st.button("Analyze") and user_input.strip():
    result = analyze_headline(user_input)
    st.write("**Sentiment Polarity:**", result['polarity'])
    st.write("**Predicted Impact:**", result['impact'])
    st.write("**Most Similar Real Headlines:**")
    st.dataframe(result['matched'])


# ===============================
# analyzer.py
# ===============================
from textblob import TextBlob
from utils import load_data, compute_similarity, compute_sentiment

def analyze_headline(headline):
    polarity = TextBlob(headline).sentiment.polarity

    if polarity > 0:
        impact = "📈 Positive - Price likely to go up"
    elif polarity < 0:
        impact = "📉 Negative - Price likely to go down"
    else:
        impact = "😐 Neutral"

    news_df = load_data("news.csv")
    news_df = compute_sentiment(news_df)
    matched = compute_similarity(news_df, headline)

    return {
        'polarity': polarity,
        'impact': impact,
        'matched': matched[['Date', 'Headline', 'sentiment', 'similarity']].head(3)
    }


# ===============================
# 📄 utils.py
# ===============================
import pandas as pd
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_data(path):
    df = pd.read_csv(path)
    df.dropna(subset=['Headline'], inplace=True)
    return df

def compute_sentiment(df):
    df['sentiment'] = df['Headline'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
    return df

def compute_similarity(df, fake_headline):
    headlines = df['Headline'].tolist()
    all_text = headlines + [fake_headline]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_text)

    sim_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    df['similarity'] = sim_scores[0]
    return df.sort_values(by='similarity', ascending=False)


# ===============================
# 📄 requirements.txt
# ===============================
streamlit
pandas
textblob
scikit-learn
yfinance


# ===============================
# 📄 README.md
# ===============================
# Fake News Impact Simulator

This project simulates how a fake news headline might impact Tesla's stock price based on sentiment analysis and historical news similarity.

## 🚀 How to Run
Run the following commands in your terminal:

```
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Files
- `app.py`: Streamlit UI
- `analyzer.py`: Sentiment + similarity backend
- `utils.py`: Data loading and similarity logic
- `news.csv`: Dataset of real news headlines
- `tesla_stock.csv`: Tesla stock prices (optional for advanced analysis)

## 📊 Example Input
> "Elon Musk announces Tesla robot army"

## 🔍 Output
- Sentiment score
- Predicted stock impact
- Matched past headlines

---

*You can extend it by adding charts, prediction confidence, and actual % price simulation using `tesla_stock.csv`.*
