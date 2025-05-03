import logging
import hashlib
import re
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import secrets
import string
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecurityError(Exception):
    """Базовый класс для ошибок безопасности"""
    pass

class ValidationError(SecurityError):
    """Ошибка валидации данных"""
    pass

class EncryptionError(SecurityError):
    """Ошибка шифрования/дешифрования"""
    pass

class SecurityManager:
    def __init__(self, key_file: str = '.security_key'):
        self.logger = logging.getLogger(__name__)
        self.key_file = Path(key_file)
        self.fernet = self._initialize_encryption()
        
    def _initialize_encryption(self) -> Fernet:
        """Инициализация шифрования"""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
            return Fernet(key)
        except Exception as e:
            self.logger.error(f'Error initializing encryption: {str(e)}')
            raise EncryptionError('Failed to initialize encryption')
            
    def encrypt_data(self, data: str) -> str:
        """Шифрование данных"""
        try:
            return self.fernet.encrypt(data.encode()).decode()
        except Exception as e:
            self.logger.error(f'Error encrypting data: {str(e)}')
            raise EncryptionError('Failed to encrypt data')
            
    def decrypt_data(self, encrypted_data: str) -> str:
        """Дешифрование данных"""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            self.logger.error(f'Error decrypting data: {str(e)}')
            raise EncryptionError('Failed to decrypt data')
            
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Генерация безопасного токена"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
        
    @staticmethod
    def hash_data(data: str) -> str:
        """Хеширование данных"""
        return hashlib.sha256(data.encode()).hexdigest()
        
    @staticmethod
    def validate_url(url: str) -> bool:
        """Валидация URL"""
        url_pattern = re.compile(
            r'^https?://'  # http:// или https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # порт
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
        
    @staticmethod
    def validate_telegram_token(token: str) -> bool:
        """Валидация токена Telegram"""
        token_pattern = re.compile(r'^\d+:[A-Za-z0-9_-]{35}$')
        return bool(token_pattern.match(token))
        
    @staticmethod
    def validate_chat_id(chat_id: str) -> bool:
        """Валидация ID чата Telegram"""
        return chat_id.isdigit() or (chat_id.startswith('-') and chat_id[1:].isdigit())
        
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Очистка текста от потенциально опасных символов"""
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        # Удаляем специальные символы
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()
        
    def secure_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Безопасное хранение конфигурации"""
        secure_config = config.copy()
        
        # Шифруем чувствительные данные
        if 'telegram_token' in secure_config:
            secure_config['telegram_token'] = self.encrypt_data(secure_config['telegram_token'])
            
        return secure_config
        
    def load_secure_config(self, config_path: str) -> Dict[str, Any]:
        """Загрузка зашифрованной конфигурации"""
        try:
            with open(config_path) as f:
                config = json.load(f)
                
            # Расшифровываем чувствительные данные
            if 'telegram_token' in config:
                config['telegram_token'] = self.decrypt_data(config['telegram_token'])
                
            return config
        except Exception as e:
            self.logger.error(f'Error loading secure config: {str(e)}')
            raise SecurityError('Failed to load secure configuration')
            
    def save_secure_config(self, config: Dict[str, Any], config_path: str):
        """Сохранение конфигурации в зашифрованном виде"""
        try:
            secure_config = self.secure_config(config)
            with open(config_path, 'w') as f:
                json.dump(secure_config, f, indent=2)
        except Exception as e:
            self.logger.error(f'Error saving secure config: {str(e)}')
            raise SecurityError('Failed to save secure configuration')
            
    def validate_review(self, review: Dict[str, Any]) -> bool:
        """Валидация данных отзыва"""
        try:
            required_fields = ['text', 'rating', 'date']
            if not all(field in review for field in required_fields):
                return False
                
            if not isinstance(review['text'], str) or not review['text'].strip():
                return False
                
            if not isinstance(review['rating'], (int, float)) or not 0 <= review['rating'] <= 5:
                return False
                
            if not isinstance(review['date'], str):
                return False
                
            return True
        except Exception:
            return False 