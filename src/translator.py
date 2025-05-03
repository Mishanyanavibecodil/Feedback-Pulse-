import logging
from typing import Optional, Dict
import json
from pathlib import Path
from googletrans import Translator
from functools import lru_cache

class TranslationError(Exception):
    """Ошибка при переводе текста"""
    pass

class TranslationCache:
    def __init__(self, cache_file: str = 'translation_cache.json'):
        self.logger = logging.getLogger(__name__)
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Dict[str, str]] = self._load_cache()
        
    def _load_cache(self) -> Dict[str, Dict[str, str]]:
        """Загрузка кэша переводов из файла"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f'Error loading translation cache: {str(e)}')
                return {}
        return {}
    
    def _save_cache(self):
        """Сохранение кэша переводов в файл"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f'Error saving translation cache: {str(e)}')
    
    def get_cached_translation(self, text: str, target_lang: str) -> Optional[str]:
        """Получение перевода из кэша"""
        return self.cache.get(text, {}).get(target_lang)
    
    def cache_translation(self, text: str, target_lang: str, translation: str):
        """Сохранение перевода в кэш"""
        if text not in self.cache:
            self.cache[text] = {}
        self.cache[text][target_lang] = translation
        self._save_cache()

class TextTranslator:
    def __init__(self, cache_file: str = 'translation_cache.json'):
        self.logger = logging.getLogger(__name__)
        self.translator = Translator()
        self.cache = TranslationCache(cache_file)
        
    @lru_cache(maxsize=1000)
    def translate(self, text: str, target_lang: str = 'en') -> str:
        """
        Перевод текста на указанный язык с использованием кэша
        
        Args:
            text: Текст для перевода
            target_lang: Целевой язык (по умолчанию английский)
            
        Returns:
            str: Переведенный текст
            
        Raises:
            TranslationError: При ошибке перевода
        """
        if not text:
            return text
            
        # Проверяем кэш
        cached = self.cache.get_cached_translation(text, target_lang)
        if cached:
            return cached
            
        try:
            # Определяем язык исходного текста
            detected = self.translator.detect(text)
            
            # Если язык уже целевой, возвращаем исходный текст
            if detected.lang == target_lang:
                self.cache.cache_translation(text, target_lang, text)
                return text
                
            # Выполняем перевод
            translation = self.translator.translate(text, dest=target_lang).text
            
            # Сохраняем в кэш
            self.cache.cache_translation(text, target_lang, translation)
            
            return translation
            
        except Exception as e:
            self.logger.error(f'Translation error: {str(e)}')
            raise TranslationError(f'Failed to translate text: {str(e)}')
            
    def translate_review(self, review_text: str, target_lang: str = 'en') -> str:
        """
        Перевод отзыва с обработкой ошибок
        
        Args:
            review_text: Текст отзыва
            target_lang: Целевой язык
            
        Returns:
            str: Переведенный текст или исходный текст при ошибке
        """
        try:
            return self.translate(review_text, target_lang)
        except TranslationError as e:
            self.logger.error(f'Error translating review: {str(e)}')
            return review_text  # Возвращаем исходный текст при ошибке 