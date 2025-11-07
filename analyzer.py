from transformers import pipeline
from utils import load_data, compute_similarity, compute_sentiment

# Load HuggingFace sentiment model (DistilBERT fine-tuned on sentiment)
sentiment_model = pipeline("sentiment-analysis")

def analyze_headline(headline):
    # Run sentiment analysis
    result = sentiment_model(headline)[0]  # returns dict: {'label': 'POSITIVE', 'score': 0.98}
    label = result['label']
    score = result['score']

    # Convert to polarity & impact message
    if label == "POSITIVE":
        impact = f" Positive ({score:.2f} confidence) - Price likely to go up"
        polarity = score
    else:
        impact = f" Negative ({score:.2f} confidence) - Price likely to go down"
        polarity = -score

    # Load dataset and compute similarity with historical headlines
    news_df = load_data("news.csv")
    news_df = compute_sentiment(news_df)  # now also transformer-based
    matched = compute_similarity(news_df, headline)

    return {
        'polarity': polarity,
        'impact': impact,
        'matched': matched[['Date', 'Headline', 'sentiment', 'similarity']].head(3)
    }
