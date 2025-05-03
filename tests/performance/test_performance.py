import pytest
import time
from src.parser import ReviewParser
from src.analyzer import SentimentAnalyzer
from src.translator import TextTranslator
import logging

@pytest.fixture
def sample_texts():
    """Создает набор тестовых текстов"""
    return [
        "Great service! Very satisfied with the experience.",
        "Terrible experience, would not recommend.",
        "Average service, nothing special.",
        "Excellent! Best service ever!",
        "Poor service, very disappointed."
    ] * 20  # Умножаем для нагрузки

class TestPerformance:
    def test_parser_performance(self):
        """Тест производительности парсера"""
        parser = ReviewParser(max_retries=1, timeout=5)
        
        # Тест инициализации
        start_time = time.time()
        parser.driver
        init_time = time.time() - start_time
        assert init_time < 5.0, "Инициализация драйвера заняла слишком много времени"
        
        # Тест очистки ресурсов
        start_time = time.time()
        parser.cleanup()
        cleanup_time = time.time() - start_time
        assert cleanup_time < 2.0, "Очистка ресурсов заняла слишком много времени"
        
    def test_analyzer_performance(self, sample_texts):
        """Тест производительности анализатора"""
        analyzer = SentimentAnalyzer(max_workers=4)
        
        # Тест одиночного анализа
        start_time = time.time()
        for text in sample_texts[:5]:
            sentiment, lang = analyzer.analyze_sentiment(text)
        single_time = time.time() - start_time
        
        # Тест пакетного анализа
        start_time = time.time()
        results = analyzer.analyze_batch(sample_texts)
        batch_time = time.time() - start_time
        
        # Проверяем, что пакетный анализ быстрее
        assert batch_time < single_time * 2, "Пакетный анализ не показал преимущества в скорости"
        
        # Тест кэширования
        start_time = time.time()
        for text in sample_texts[:5]:
            sentiment, lang = analyzer.analyze_sentiment(text)
        cached_time = time.time() - start_time
        
        # Проверяем, что кэшированный анализ быстрее
        assert cached_time < single_time, "Кэширование не показало преимущества в скорости"
        
    def test_translator_performance(self, sample_texts):
        """Тест производительности переводчика"""
        translator = TextTranslator()
        
        # Тест одиночного перевода
        start_time = time.time()
        for text in sample_texts[:5]:
            translated = translator.translate(text, 'ru')
        single_time = time.time() - start_time
        
        # Тест кэширования
        start_time = time.time()
        for text in sample_texts[:5]:
            translated = translator.translate(text, 'ru')
        cached_time = time.time() - start_time
        
        # Проверяем, что кэшированный перевод быстрее
        assert cached_time < single_time, "Кэширование перевода не показало преимущества в скорости"
        
    def test_memory_usage(self, sample_texts):
        """Тест использования памяти"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Создаем и используем компоненты
        analyzer = SentimentAnalyzer()
        translator = TextTranslator()
        
        # Анализируем тексты
        for text in sample_texts:
            sentiment, lang = analyzer.analyze_sentiment(text)
            if lang != 'en':
                translated = translator.translate(text, 'en')
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Проверяем, что увеличение памяти не превышает 100MB
        assert memory_increase < 100 * 1024 * 1024, "Слишком большое потребление памяти"
        
    def test_concurrent_load(self, sample_texts):
        """Тест под нагрузкой"""
        import concurrent.futures
        
        analyzer = SentimentAnalyzer(max_workers=4)
        translator = TextTranslator()
        
        def process_text(text):
            sentiment, lang = analyzer.analyze_sentiment(text)
            if lang != 'en':
                translated = translator.translate(text, 'en')
            return sentiment, lang
        
        # Запускаем множество потоков
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_text, text) for text in sample_texts * 2]
            results = [f.result() for f in futures]
        total_time = time.time() - start_time
        
        # Проверяем, что обработка не заняла слишком много времени
        assert total_time < 30.0, "Обработка под нагрузкой заняла слишком много времени"
        
        # Проверяем, что все результаты получены
        assert len(results) == len(sample_texts) * 2, "Не все результаты были получены" 