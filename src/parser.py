import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    StaleElementReferenceException
)
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import atexit

@dataclass
class Review:
    text: str
    rating: float
    author: str
    date: str

class ParserError(Exception):
    """Базовый класс для ошибок парсера"""
    pass

class NetworkError(ParserError):
    """Ошибка сети или загрузки страницы"""
    pass

class ParsingError(ParserError):
    """Ошибка парсинга данных"""
    pass

class ReviewParser:
    def __init__(self, max_retries: int = 3, timeout: int = 10, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_workers = max_workers
        self._driver = None
        self._wait = None
        # Регистрируем очистку при выходе
        atexit.register(self.cleanup)
        
    @property
    def driver(self):
        """Ленивая инициализация драйвера"""
        if self._driver is None:
            try:
                options = webdriver.ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-infobars')
                options.add_argument('--disable-notifications')
                options.add_argument('--disable-popup-blocking')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                service = Service(ChromeDriverManager().install())
                self._driver = webdriver.Chrome(service=service, options=options)
                self._driver.set_page_load_timeout(self.timeout)
                self._wait = WebDriverWait(self._driver, self.timeout)
            except Exception as e:
                self.logger.error(f'Failed to initialize Chrome driver: {str(e)}')
                raise NetworkError('Failed to initialize Chrome driver') from e
        return self._driver
        
    @property
    def wait(self):
        """Ленивая инициализация WebDriverWait"""
        if self._wait is None:
            self._wait = WebDriverWait(self.driver, self.timeout)
        return self._wait
        
    def __del__(self):
        """Очистка ресурсов при удалении объекта"""
        self.cleanup()
        
    def cleanup(self):
        """Очистка ресурсов"""
        if self._driver:
            try:
                self._driver.quit()
            except Exception as e:
                self.logger.error(f'Error during driver cleanup: {str(e)}')
            finally:
                self._driver = None
                self._wait = None
                
    @lru_cache(maxsize=100)
    def _get_element_text(self, element, selector: str) -> Optional[str]:
        """Получение текста элемента с кэшированием"""
        try:
            return element.find_element(By.CSS_SELECTOR, selector).text.strip()
        except NoSuchElementException:
            return None
        except StaleElementReferenceException:
            self.logger.warning(f'Stale element reference for selector: {selector}')
            return None
            
    def _parse_review_element(self, element) -> Optional[Review]:
        """Парсинг отдельного отзыва с обработкой ошибок"""
        try:
            text = self._get_element_text(element, '.review-text')
            if not text:
                return None
                
            rating_text = self._get_element_text(element, '.rating')
            if not rating_text:
                return None
                
            try:
                rating = float(rating_text.split()[0])
                if not 0 <= rating <= 5:
                    self.logger.warning(f'Invalid rating value: {rating}')
                    return None
            except (ValueError, IndexError):
                return None
                
            author = self._get_element_text(element, '.author-name') or 'Anonymous'
            date = self._get_element_text(element, '.review-date') or datetime.now().strftime('%Y-%m-%d')
            
            return Review(text=text, rating=rating, author=author, date=date)
        except StaleElementReferenceException:
            self.logger.warning('Stale element reference while parsing review')
            return None
        except Exception as e:
            self.logger.error(f'Error parsing review element: {str(e)}')
            return None
            
    def _load_reviews(self, url: str) -> List[Review]:
        """Загрузка и парсинг отзывов с использованием многопоточности"""
        try:
            self.driver.get(url)
            time.sleep(2)  # Даем время для загрузки динамического контента
            
            # Ждем загрузки отзывов
            review_elements = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.review-container'))
            )
            
            if not review_elements:
                self.logger.warning('No reviews found on the page')
                return []
            
            # Парсим отзывы в нескольких потоках
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                reviews = list(filter(None, executor.map(self._parse_review_element, review_elements)))
                
            return reviews
        except TimeoutException:
            raise NetworkError('Timeout while loading reviews')
        except WebDriverException as e:
            raise NetworkError(f'WebDriver error: {str(e)}')
        except Exception as e:
            raise ParsingError(f'Error parsing reviews: {str(e)}')
            
    def parse_reviews(self, url: str) -> List[Review]:
        """Парсинг отзывов с повторными попытками"""
        for attempt in range(self.max_retries):
            try:
                return self._load_reviews(url)
            except NetworkError as e:
                if attempt == self.max_retries - 1:
                    raise
                self.logger.warning(f'Network error, retrying ({attempt + 1}/{self.max_retries}): {str(e)}')
                time.sleep(2 ** attempt)  # Экспоненциальная задержка
                self.cleanup()  # Пересоздаем драйвер при ошибке
            except Exception as e:
                self.logger.error(f'Unexpected error: {str(e)}')
                raise