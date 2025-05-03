import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from src.parser import ReviewParser, Review, NetworkError, ParsingError
from src.analyzer import SentimentAnalyzer
from src.translator import TextTranslator
from src.notifier import TelegramNotifier
from src.security import SecurityManager, SecurityError, ValidationError
from src.logger import setup_logging, log_error, log_performance
from src.config import ConfigManager
import concurrent.futures
from collections import defaultdict
import time

def load_config(security_manager: SecurityManager) -> dict:
    """Загрузка конфигурации с проверкой безопасности"""
    try:
        config = security_manager.load_secure_config('config.json')
        logging.info('Конфигурация загружена', extra={'config_keys': list(config.keys())})
        return config
    except SecurityError as e:
        log_error(logging.getLogger(__name__), 'Ошибка безопасности при загрузке конфигурации', e)
        raise
    except ValidationError as e:
        log_error(logging.getLogger(__name__), 'Ошибка валидации конфигурации', e)
        raise
    except Exception as e:
        log_error(logging.getLogger(__name__), 'Неожиданная ошибка при загрузке конфигурации', e)
        raise

def load_cache(security_manager: SecurityManager) -> list:
    """Загрузка кэша с проверкой безопасности"""
    try:
        cache = security_manager.load_secure_cache('reviews_cache.json')
        logging.info('Кэш загружен', extra={'cache_size': len(cache)})
        return cache
    except SecurityError as e:
        log_error(logging.getLogger(__name__), 'Ошибка безопасности при загрузке кэша', e)
        return []
    except ValidationError as e:
        log_error(logging.getLogger(__name__), 'Ошибка валидации кэша', e)
        return []
    except Exception as e:
        log_error(logging.getLogger(__name__), 'Неожиданная ошибка при загрузке кэша', e)
        return []

def save_cache(security_manager: SecurityManager, cache: list) -> None:
    """Сохранение кэша с проверкой безопасности"""
    try:
        security_manager.save_secure_cache('reviews_cache.json', cache)
        logging.info('Кэш сохранен', extra={'cache_size': len(cache)})
    except Exception as e:
        log_error(logging.getLogger(__name__), 'Ошибка при сохранении кэша', e)

def process_reviews_batch(
    parser: ReviewParser,
    analyzer: SentimentAnalyzer,
    security_manager: SecurityManager,
    url: str,
    cache: list
) -> list:
    """Обработка пакета отзывов"""
    start_time = time.time()
    try:
        # Получаем отзывы
        reviews = parser.parse_reviews(url)
        log_performance(
            logging.getLogger(__name__),
            'parsing_reviews',
            time.time() - start_time,
            {'reviews_count': len(reviews)}
        )
        
        # Фильтруем новые отзывы
        new_reviews = []
        for review in reviews:
            review_hash = security_manager.hash_data(review.text)
            if not any(cached['hash'] == review_hash for cached in cache):
                new_reviews.append(review)
        
        if not new_reviews:
            logging.info('Новых отзывов не найдено')
            return cache
            
        # Анализируем отзывы
        analysis_start = time.time()
        for review in new_reviews:
            try:
                # Валидируем отзыв
                security_manager.validate_review(review)
                
                # Анализируем тональность
                sentiment, lang = analyzer.analyze_sentiment(review.text)
                
                # Добавляем в кэш
                cache.append({
                    'text': review.text,
                    'hash': security_manager.hash_data(review.text),
                    'sentiment': sentiment,
                    'language': lang,
                    'rating': review.rating,
                    'author': review.author,
                    'date': review.date
                })
                
                # Логируем информацию об отзыве
                logging.info(
                    'Обработан отзыв',
                    extra={
                        'sentiment': sentiment,
                        'language': lang,
                        'rating': review.rating,
                        'author': review.author
                    }
                )
                
            except ValidationError as e:
                log_error(
                    logging.getLogger(__name__),
                    f'Отзыв не прошел валидацию: {review.text[:100]}...',
                    e
                )
            except Exception as e:
                log_error(
                    logging.getLogger(__name__),
                    f'Ошибка при обработке отзыва: {review.text[:100]}...',
                    e
                )
        
        log_performance(
            logging.getLogger(__name__),
            'analyzing_reviews',
            time.time() - analysis_start,
            {'reviews_count': len(new_reviews)}
        )
        
        return cache
        
    except NetworkError as e:
        log_error(logging.getLogger(__name__), 'Ошибка сети при получении отзывов', e)
        return cache
    except ParsingError as e:
        log_error(logging.getLogger(__name__), 'Ошибка парсинга отзывов', e)
        return cache
    except Exception as e:
        log_error(logging.getLogger(__name__), 'Неожиданная ошибка при обработке отзывов', e)
        return cache

def main():
    """Основная функция программы"""
    try:
        # Загружаем конфигурацию
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Настраиваем логирование
        logging_config = config_manager.get_logging_config()
        setup_logging(
            log_dir=logging_config.directory,
            log_level=getattr(logging, logging_config.level),
            max_bytes=logging_config.max_bytes,
            backup_count=logging_config.backup_count
        )
        
        # Инициализируем компоненты
        security_manager = SecurityManager()
        
        parser_config = config_manager.get_parser_config()
        parser = ReviewParser(
            max_retries=parser_config.max_retries,
            timeout=parser_config.timeout,
            max_workers=parser_config.max_workers
        )
        
        analyzer_config = config_manager.get_analyzer_config()
        analyzer = SentimentAnalyzer(
            target_language=analyzer_config.target_language,
            min_confidence=analyzer_config.min_confidence,
            batch_size=analyzer_config.batch_size
        )
        
        notifier_config = config_manager.get_notifier_config()
        if notifier_config.enabled:
            notifier = TelegramNotifier(
                token=notifier_config.telegram_token,
                chat_id=notifier_config.chat_id
            )
            if notifier_config.notify_on_startup:
                notifier.send_message('Программа запущена')
        
        # Загружаем кэш
        cache_config = config_manager.get_cache_config()
        if cache_config.enabled:
            cache = load_cache(security_manager)
        else:
            cache = []
        
        # Обрабатываем отзывы
        cache = process_reviews_batch(
            parser=parser,
            analyzer=analyzer,
            security_manager=security_manager,
            url=config['google_maps_url'],
            cache=cache
        )
        
        # Сохраняем кэш
        if cache_config.enabled:
            save_cache(security_manager, cache)
        
        # Логируем статистику
        if cache:
            sentiments = [review['sentiment'] for review in cache]
            languages = [review['language'] for review in cache]
            
            logging.info(
                'Статистика обработки',
                extra={
                    'total_reviews': len(cache),
                    'average_sentiment': sum(sentiments) / len(sentiments),
                    'languages': list(set(languages))
                }
            )
            
            # Отправляем уведомление о завершении
            if notifier_config.enabled and notifier_config.notify_on_shutdown:
                notifier.send_message(
                    f'Обработка завершена\n'
                    f'Всего отзывов: {len(cache)}\n'
                    f'Средняя тональность: {sum(sentiments) / len(sentiments):.2f}\n'
                    f'Языки: {", ".join(set(languages))}'
                )
        
    except Exception as e:
        log_error(logging.getLogger(__name__), 'Критическая ошибка в работе программы', e)
        if notifier_config.enabled and notifier_config.notify_on_error:
            notifier.send_message(f'Произошла ошибка: {str(e)}')
        raise
    finally:
        # Очищаем ресурсы
        parser.cleanup()

if __name__ == '__main__':
    main()