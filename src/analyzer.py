import logging
from typing import Tuple, Optional, Dict, List
from textblob import TextBlob
from langdetect import detect, LangDetectException
from src.translator import TextTranslator
import re
from functools import lru_cache
import concurrent.futures
from collections import defaultdict
import threading

class SentimentAnalyzer:
    def __init__(self, target_language: str = 'en', max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.target_language = target_language
        self.max_workers = max_workers
        self.translator = TextTranslator()
        self._sentiment_cache = {}
        self._language_cache = {}
        self._cache_lock = threading.Lock()
        
    @lru_cache(maxsize=1000)
    def _detect_language(self, text: str) -> str:
        """Определение языка текста с кэшированием"""
        if not text or not isinstance(text, str):
            return 'unknown'
            
        try:
            return detect(text)
        except LangDetectException:
            self.logger.warning('Could not detect language')
            return 'unknown'
        except Exception as e:
            self.logger.warning(f'Error detecting language: {str(e)}')
            return 'unknown'
            
    @lru_cache(maxsize=1000)
    def _get_sentiment(self, text: str) -> float:
        """Получение тональности текста с кэшированием"""
        if not text or not isinstance(text, str):
            return 0.0
            
        try:
            return TextBlob(text).sentiment.polarity
        except Exception as e:
            self.logger.error(f'Error analyzing sentiment: {str(e)}')
            return 0.0
            
    def _preprocess_text(self, text: str) -> str:
        """Предобработка текста"""
        if not text or not isinstance(text, str):
            return ''
            
        # Удаляем специальные символы и лишние пробелы
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """Анализ тональности текста с определением языка"""
        if not text or not isinstance(text, str):
            return 0.0, 'unknown'
            
        try:
            # Предобработка текста
            text = self._preprocess_text(text)
            if not text:
                return 0.0, 'unknown'
            
            # Определяем язык
            detected_lang = self._detect_language(text)
            
            # Если язык не английский, переводим
            if detected_lang != self.target_language:
                try:
                    text = self.translator.translate(text, self.target_language)
                except Exception as e:
                    self.logger.error(f'Translation error: {str(e)}')
                    return 0.0, detected_lang
                
            # Анализируем тональность
            sentiment = self._get_sentiment(text)
            
            return sentiment, detected_lang
            
        except Exception as e:
            self.logger.error(f'Error in sentiment analysis: {str(e)}')
            return 0.0, 'unknown'
            
    def analyze_batch(self, texts: List[str]) -> List[Tuple[float, str]]:
        """Пакетный анализ тональности"""
        if not texts:
            return []
            
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_text = {executor.submit(self.analyze_sentiment, text): text for text in texts}
            for future in concurrent.futures.as_completed(future_to_text):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f'Error in batch analysis: {str(e)}')
                    results.append((0.0, 'unknown'))
        return results
        
    def get_sentiment_stats(self, texts: List[str]) -> Dict[str, float]:
        """Получение статистики по тональности"""
        if not texts:
            return {
                'average': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 0.0
            }
            
        sentiments = self.analyze_batch(texts)
        total = len(sentiments)
        
        if total == 0:
            return {
                'average': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 0.0
            }
        
        stats = {
            'average': sum(s[0] for s in sentiments) / total,
            'positive': sum(1 for s in sentiments if s[0] > 0.3) / total,
            'negative': sum(1 for s in sentiments if s[0] < -0.3) / total,
            'neutral': sum(1 for s in sentiments if -0.3 <= s[0] <= 0.3) / total
        }
        
        return stats
        
    def get_language_distribution(self, texts: List[str]) -> Dict[str, int]:
        """Получение распределения по языкам"""
        if not texts:
            return {}
            
        language_counts = defaultdict(int)
        for text in texts:
            if text and isinstance(text, str):
                lang = self._detect_language(text)
                language_counts[lang] += 1
        return dict(language_counts)
        
    def get_sentiment_label(self, sentiment: float) -> str:
        """Получение текстовой метки тональности"""
        if not isinstance(sentiment, (int, float)):
            return 'neutral'
            
        if sentiment > 0.3:
            return 'positive'
        elif sentiment < -0.3:
            return 'negative'
        else:
            return 'neutral'