import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class StructuredLogFormatter(logging.Formatter):
    """Форматтер для структурированного логирования в JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Добавляем дополнительные поля, если они есть
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
            
        # Добавляем информацию об исключении, если оно есть
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_logging(
    log_dir: str = 'logs',
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Настраивает систему логирования
    
    Args:
        log_dir: Директория для хранения логов
        log_level: Уровень логирования
        max_bytes: Максимальный размер файла лога
        backup_count: Количество файлов для ротации
    """
    # Создаем директорию для логов, если её нет
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Создаем обработчики для разных уровней логирования
    handlers = {
        'debug': logging.handlers.RotatingFileHandler(
            log_path / 'debug.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        ),
        'info': logging.handlers.RotatingFileHandler(
            log_path / 'info.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        ),
        'error': logging.handlers.RotatingFileHandler(
            log_path / 'error.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        ),
        'console': logging.StreamHandler()
    }
    
    # Настраиваем форматтеры
    json_formatter = StructuredLogFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Устанавливаем уровни и форматтеры для обработчиков
    handlers['debug'].setLevel(logging.DEBUG)
    handlers['debug'].setFormatter(json_formatter)
    
    handlers['info'].setLevel(logging.INFO)
    handlers['info'].setFormatter(json_formatter)
    
    handlers['error'].setLevel(logging.ERROR)
    handlers['error'].setFormatter(json_formatter)
    
    handlers['console'].setLevel(logging.INFO)
    handlers['console'].setFormatter(console_formatter)
    
    # Добавляем обработчики к корневому логгеру
    for handler in handlers.values():
        root_logger.addHandler(handler)
    
    # Логируем информацию о запуске
    logging.info('Логирование настроено', extra={
        'log_dir': str(log_path),
        'log_level': logging.getLevelName(log_level),
        'max_bytes': max_bytes,
        'backup_count': backup_count
    })

def log_error(
    logger: logging.Logger,
    message: str,
    error: Exception,
    extra: Dict[str, Any] = None
) -> None:
    """Логирует ошибку с дополнительной информацией
    
    Args:
        logger: Логгер для записи
        message: Сообщение об ошибке
        error: Объект исключения
        extra: Дополнительные поля для логирования
    """
    extra = extra or {}
    extra.update({
        'error_type': error.__class__.__name__,
        'error_message': str(error)
    })
    logger.error(message, exc_info=True, extra=extra)

def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    extra: Dict[str, Any] = None
) -> None:
    """Логирует информацию о производительности
    
    Args:
        logger: Логгер для записи
        operation: Название операции
        duration: Длительность операции в секундах
        extra: Дополнительные поля для логирования
    """
    extra = extra or {}
    extra.update({
        'operation': operation,
        'duration': duration
    })
    logger.info(f'Операция {operation} выполнена за {duration:.2f} секунд', extra=extra) 