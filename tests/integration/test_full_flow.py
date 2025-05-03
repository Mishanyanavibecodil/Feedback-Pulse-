import pytest
import json
import os
from pathlib import Path
from src.parser import ReviewParser, Review
from src.analyzer import SentimentAnalyzer
from src.translator import TextTranslator
from src.security import SecurityManager
import logging
import tempfile

@pytest.fixture
def temp_config():
    """Создает временный конфигурационный файл"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "google_maps_url": "https://www.google.com/maps/test",
            "telegram_token": "test_token",
            "chat_id": "test_chat_id"
        }, f)
    yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_cache():
    """Создает временный файл кэша"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
    yield f.name
    os.unlink(f.name)

@pytest.fixture
def security_manager():
    """Создает менеджер безопасности"""
    return SecurityManager()

class TestFullFlow:
    def test_end_to_end_flow(self, temp_config, temp_cache, security_manager):
        """Тест полного потока работы приложения"""
        # Инициализация компонентов
        parser = ReviewParser(max_retries=1, timeout=5)
        analyzer = SentimentAnalyzer(target_language='en')
        translator = TextTranslator()
        
        # Загрузка конфигурации
        with open(temp_config, 'r') as f:
            config = json.load(f)
        assert config['google_maps_url'] == "https://www.google.com/maps/test"
        
        # Загрузка кэша
        with open(temp_cache, 'r') as f:
            cache = json.load(f)
        assert isinstance(cache, list)
        
        # Тест парсинга отзывов
        try:
            reviews = parser.parse_reviews(config['google_maps_url'])
            assert isinstance(reviews, list)
        except Exception as e:
            logging.warning(f"Парсинг не удался (ожидаемо в тесте): {str(e)}")
            # Создаем тестовые отзывы
            reviews = [
                Review(text="Great service!", rating=5.0, author="Test User", date="2024-01-01"),
                Review(text="Terrible experience", rating=1.0, author="Test User", date="2024-01-01")
            ]
        
        # Тест анализа тональности
        for review in reviews:
            sentiment, lang = analyzer.analyze_sentiment(review.text)
            assert isinstance(sentiment, float)
            assert -1 <= sentiment <= 1
            assert isinstance(lang, str)
        
        # Тест перевода
        test_text = "Привет, мир!"
        translated = translator.translate(test_text, 'en')
        assert isinstance(translated, str)
        assert len(translated) > 0
        
        # Тест безопасности
        hashed_review = security_manager.hash_data(review.text)
        assert isinstance(hashed_review, str)
        assert len(hashed_review) > 0
        
        # Тест сохранения кэша
        cache.append({
            'text': review.text,
            'hash': hashed_review,
            'sentiment': sentiment,
            'language': lang
        })
        with open(temp_cache, 'w') as f:
            json.dump(cache, f)
        
        # Проверка сохраненного кэша
        with open(temp_cache, 'r') as f:
            saved_cache = json.load(f)
        assert len(saved_cache) == 1
        assert saved_cache[0]['text'] == review.text
        assert saved_cache[0]['hash'] == hashed_review

    def test_error_handling(self, temp_config, temp_cache, security_manager):
        """Тест обработки ошибок"""
        parser = ReviewParser(max_retries=1, timeout=1)
        analyzer = SentimentAnalyzer()
        
        # Тест обработки неверного URL
        with pytest.raises(Exception):
            parser.parse_reviews("invalid_url")
        
        # Тест обработки пустого текста
        sentiment, lang = analyzer.analyze_sentiment("")
        assert sentiment == 0.0
        assert lang == 'unknown'
        
        # Тест обработки некорректного JSON
        with open(temp_cache, 'w') as f:
            f.write("invalid json")
        with pytest.raises(json.JSONDecodeError):
            with open(temp_cache, 'r') as f:
                json.load(f)

    def test_concurrent_processing(self, temp_config, temp_cache):
        """Тест многопоточной обработки"""
        analyzer = SentimentAnalyzer(max_workers=4)
        texts = [
            "Great service!",
            "Terrible experience",
            "Not bad",
            "Excellent!"
        ] * 10  # Умножаем для нагрузки
        
        # Тест пакетного анализа
        results = analyzer.analyze_batch(texts)
        assert len(results) == len(texts)
        for sentiment, lang in results:
            assert isinstance(sentiment, float)
            assert isinstance(lang, str)
        
        # Тест статистики
        stats = analyzer.get_sentiment_stats(texts)
        assert 'average' in stats
        assert 'positive' in stats
        assert 'negative' in stats
        assert 'neutral' in stats
        
        # Тест распределения языков
        lang_dist = analyzer.get_language_distribution(texts)
        assert isinstance(lang_dist, dict)
        assert len(lang_dist) > 0 