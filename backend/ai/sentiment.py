 
from transformers import pipeline

# Load the sentiment-analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_sentiment(text):
    """
    Takes text input and returns sentiment label and score.
    """
    result = sentiment_pipeline(text)
    return result[0]  # result is a list of one dict
