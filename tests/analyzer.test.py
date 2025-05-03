import pytest
from src.analyzer import SentimentAnalyzer

def test_sentiment_analysis_english():
    analyzer = SentimentAnalyzer()
    
    # Тест негативного отзыва
    sentiment = analyzer.analyze_sentiment("This is terrible!")
    assert sentiment < -0.3
    
    # Тест позитивного отзыва
    sentiment = analyzer.analyze_sentiment("This is excellent!")
    assert sentiment > 0.3
    
    # Тест нейтрального отзыва
    sentiment = analyzer.analyze_sentiment("This is okay")
    assert abs(sentiment) <= 0.3

def test_sentiment_analysis_russian():
    analyzer = SentimentAnalyzer()
    
    # Тест негативного отзыва
    sentiment = analyzer.analyze_sentiment("Ужасно!")
    assert sentiment < -0.3
    
    # Тест позитивного отзыва
    sentiment = analyzer.analyze_sentiment("Отлично!")
    assert sentiment > 0.3
    
    # Тест нейтрального отзыва
    sentiment = analyzer.analyze_sentiment("Нормально")
    assert abs(sentiment) <= 0.3

def test_sentiment_analysis_empty_text():
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze_sentiment("")
    assert sentiment == 0.0

def test_sentiment_analysis_none_text():
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze_sentiment(None)
    assert sentiment == 0.0

def test_sentiment_analysis_invalid_input():
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze_sentiment(123)  # Не строка
    assert sentiment == 0.0

def test_sentiment_analysis_mixed_language():
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze_sentiment("This is отлично!")
    assert sentiment > 0.3  # Должен определить как позитивный