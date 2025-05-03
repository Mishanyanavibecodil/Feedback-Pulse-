import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from src.logger import log_error

@dataclass
class ParserConfig:
    """Конфигурация парсера"""
    max_retries: int = 3
    timeout: int = 10
    max_workers: int = 4
    scroll_pause_time: float = 2.0
    max_reviews: Optional[int] = None
    min_rating: float = 0.0
    max_rating: float = 5.0

@dataclass
class AnalyzerConfig:
    """Конфигурация анализатора"""
    target_language: str = 'en'
    min_confidence: float = 0.6
    batch_size: int = 10
    cache_size: int = 1000
    sentiment_thresholds: Dict[str, float] = None

    def __post_init__(self):
        if self.sentiment_thresholds is None:
            self.sentiment_thresholds = {
                'positive': 0.3,
                'negative': -0.3,
                'neutral': 0.0
            }

@dataclass
class NotifierConfig:
    """Конфигурация уведомлений"""
    enabled: bool = True
    telegram_token: str = ''
    chat_id: str = ''
    notify_on_negative: bool = True
    notify_on_error: bool = True
    notify_on_startup: bool = True
    notify_on_shutdown: bool = True

@dataclass
class CacheConfig:
    """Конфигурация кэширования"""
    enabled: bool = True
    max_size: int = 1000
    ttl_days: int = 30
    compression: bool = True
    backup_count: int = 5

@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    level: str = 'INFO'
    directory: str = 'logs'
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = 'json'
    console_output: bool = True

@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    hash_algorithm: str = 'sha256'
    min_password_length: int = 8
    max_login_attempts: int = 3
    session_timeout: int = 3600
    allowed_ips: list = None

    def __post_init__(self):
        if self.allowed_ips is None:
            self.allowed_ips = ['127.0.0.1']

class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = Path(config_path)
        self.parser_config = ParserConfig()
        self.analyzer_config = AnalyzerConfig()
        self.notifier_config = NotifierConfig()
        self.cache_config = CacheConfig()
        self.logging_config = LoggingConfig()
        self.security_config = SecurityConfig()
        
    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        try:
            if not self.config_path.exists():
                self._create_default_config()
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self._validate_config(config)
            self._update_configs(config)
            
            logging.info('Конфигурация успешно загружена')
            return config
            
        except Exception as e:
            log_error(logging.getLogger(__name__), 'Ошибка загрузки конфигурации', e)
            raise
            
    def save_config(self, config: Dict[str, Any]) -> None:
        """Сохраняет конфигурацию в файл"""
        try:
            self._validate_config(config)
            
            # Создаем резервную копию
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                self.config_path.rename(backup_path)
                
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            self._update_configs(config)
            logging.info('Конфигурация успешно сохранена')
            
        except Exception as e:
            log_error(logging.getLogger(__name__), 'Ошибка сохранения конфигурации', e)
            raise
            
    def _create_default_config(self) -> None:
        """Создает конфигурацию по умолчанию"""
        default_config = {
            'parser': {
                'max_retries': self.parser_config.max_retries,
                'timeout': self.parser_config.timeout,
                'max_workers': self.parser_config.max_workers,
                'scroll_pause_time': self.parser_config.scroll_pause_time,
                'max_reviews': self.parser_config.max_reviews,
                'min_rating': self.parser_config.min_rating,
                'max_rating': self.parser_config.max_rating
            },
            'analyzer': {
                'target_language': self.analyzer_config.target_language,
                'min_confidence': self.analyzer_config.min_confidence,
                'batch_size': self.analyzer_config.batch_size,
                'cache_size': self.analyzer_config.cache_size,
                'sentiment_thresholds': self.analyzer_config.sentiment_thresholds
            },
            'notifier': {
                'enabled': self.notifier_config.enabled,
                'telegram_token': self.notifier_config.telegram_token,
                'chat_id': self.notifier_config.chat_id,
                'notify_on_negative': self.notifier_config.notify_on_negative,
                'notify_on_error': self.notifier_config.notify_on_error,
                'notify_on_startup': self.notifier_config.notify_on_startup,
                'notify_on_shutdown': self.notifier_config.notify_on_shutdown
            },
            'cache': {
                'enabled': self.cache_config.enabled,
                'max_size': self.cache_config.max_size,
                'ttl_days': self.cache_config.ttl_days,
                'compression': self.cache_config.compression,
                'backup_count': self.cache_config.backup_count
            },
            'logging': {
                'level': self.logging_config.level,
                'directory': self.logging_config.directory,
                'max_bytes': self.logging_config.max_bytes,
                'backup_count': self.logging_config.backup_count,
                'format': self.logging_config.format,
                'console_output': self.logging_config.console_output
            },
            'security': {
                'hash_algorithm': self.security_config.hash_algorithm,
                'min_password_length': self.security_config.min_password_length,
                'max_login_attempts': self.security_config.max_login_attempts,
                'session_timeout': self.security_config.session_timeout,
                'allowed_ips': self.security_config.allowed_ips
            }
        }
        
        self.save_config(default_config)
        
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Валидирует конфигурацию"""
        required_sections = ['parser', 'analyzer', 'notifier', 'cache', 'logging', 'security']
        
        # Проверяем наличие всех секций
        for section in required_sections:
            if section not in config:
                raise ValueError(f'Отсутствует секция {section} в конфигурации')
                
        # Валидация парсера
        parser = config['parser']
        if not isinstance(parser.get('max_retries'), int) or parser['max_retries'] < 1:
            raise ValueError('max_retries должен быть положительным целым числом')
        if not isinstance(parser.get('timeout'), int) or parser['timeout'] < 1:
            raise ValueError('timeout должен быть положительным целым числом')
            
        # Валидация анализатора
        analyzer = config['analyzer']
        if not isinstance(analyzer.get('min_confidence'), (int, float)) or not 0 <= analyzer['min_confidence'] <= 1:
            raise ValueError('min_confidence должен быть числом от 0 до 1')
            
        # Валидация уведомлений
        notifier = config['notifier']
        if notifier.get('enabled'):
            if not notifier.get('telegram_token'):
                raise ValueError('telegram_token обязателен при включенных уведомлениях')
            if not notifier.get('chat_id'):
                raise ValueError('chat_id обязателен при включенных уведомлениях')
                
        # Валидация кэша
        cache = config['cache']
        if not isinstance(cache.get('max_size'), int) or cache['max_size'] < 1:
            raise ValueError('max_size должен быть положительным целым числом')
            
        # Валидация логирования
        logging_config = config['logging']
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if logging_config.get('level') not in valid_levels:
            raise ValueError(f'level должен быть одним из: {", ".join(valid_levels)}')
            
    def _update_configs(self, config: Dict[str, Any]) -> None:
        """Обновляет конфигурации из словаря"""
        self.parser_config = ParserConfig(**config['parser'])
        self.analyzer_config = AnalyzerConfig(**config['analyzer'])
        self.notifier_config = NotifierConfig(**config['notifier'])
        self.cache_config = CacheConfig(**config['cache'])
        self.logging_config = LoggingConfig(**config['logging'])
        self.security_config = SecurityConfig(**config['security'])
        
    def get_parser_config(self) -> ParserConfig:
        """Возвращает конфигурацию парсера"""
        return self.parser_config
        
    def get_analyzer_config(self) -> AnalyzerConfig:
        """Возвращает конфигурацию анализатора"""
        return self.analyzer_config
        
    def get_notifier_config(self) -> NotifierConfig:
        """Возвращает конфигурацию уведомлений"""
        return self.notifier_config
        
    def get_cache_config(self) -> CacheConfig:
        """Возвращает конфигурацию кэша"""
        return self.cache_config
        
    def get_logging_config(self) -> LoggingConfig:
        """Возвращает конфигурацию логирования"""
        return self.logging_config
        
    def get_security_config(self) -> SecurityConfig:
        """Возвращает конфигурацию безопасности"""
        return self.security_config 