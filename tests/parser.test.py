import pytest
from unittest.mock import Mock, patch
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException
)
from src.parser import ReviewParser, Review, NetworkError, ParsingError

@pytest.fixture
def mock_driver():
    with patch('src.parser.webdriver.Chrome') as mock_chrome:
        driver = Mock()
        driver.page_source = '''
        <div class="ODSEW-ShBeI NIyLF-haAclf gm2-body-2">
            <span class="ODSEW-ShBeI-text">Test review</span>
            <span class="ODSEW-ShBeI-H1e3jb" aria-label="Rating 4.0"></span>
            <span class="ODSEW-ShBeI-RgZmSc-date">2024-01-01</span>
            <span class="ODSEW-ShBeI-title">Test Author</span>
        </div>
        '''
        mock_chrome.return_value = driver
        yield driver

def test_parser_returns_valid_data(mock_driver):
    parser = ReviewParser()
    reviews = parser.parse_reviews('test_url')
    
    assert isinstance(reviews, list)
    assert len(reviews) > 0
    
    review = reviews[0]
    assert isinstance(review, Review)
    assert review.text == 'Test review'
    assert review.rating == 4.0
    assert review.date == '2024-01-01'
    assert review.author == 'Test Author'
    assert review.source == 'google_maps'

def test_parser_handles_empty_response(mock_driver):
    mock_driver.page_source = ''
    parser = ReviewParser()
    reviews = parser.parse_reviews('test_url')
    
    assert isinstance(reviews, list)
    assert len(reviews) == 0

def test_parser_handles_missing_elements(mock_driver):
    mock_driver.page_source = '''
    <div class="ODSEW-ShBeI NIyLF-haAclf gm2-body-2">
        <span class="ODSEW-ShBeI-text">Test review</span>
    </div>
    '''
    parser = ReviewParser()
    reviews = parser.parse_reviews('test_url')
    
    assert isinstance(reviews, list)
    assert len(reviews) == 0

def test_parser_handles_invalid_rating(mock_driver):
    mock_driver.page_source = '''
    <div class="ODSEW-ShBeI NIyLF-haAclf gm2-body-2">
        <span class="ODSEW-ShBeI-text">Test review</span>
        <span class="ODSEW-ShBeI-H1e3jb" aria-label="Invalid rating"></span>
        <span class="ODSEW-ShBeI-RgZmSc-date">2024-01-01</span>
    </div>
    '''
    parser = ReviewParser()
    reviews = parser.parse_reviews('test_url')
    
    assert isinstance(reviews, list)
    assert len(reviews) == 0

def test_parser_handles_timeout(mock_driver):
    mock_driver.get.side_effect = TimeoutException()
    parser = ReviewParser(max_retries=1)
    
    with pytest.raises(NetworkError) as exc_info:
        parser.parse_reviews('test_url')
    assert "Failed to load reviews page" in str(exc_info.value)

def test_parser_handles_webdriver_error(mock_driver):
    mock_driver.get.side_effect = WebDriverException("Test error")
    parser = ReviewParser(max_retries=1)
    
    with pytest.raises(NetworkError) as exc_info:
        parser.parse_reviews('test_url')
    assert "WebDriver error occurred" in str(exc_info.value)

def test_parser_handles_stale_element(mock_driver):
    mock_driver.page_source = '''
    <div class="ODSEW-ShBeI NIyLF-haAclf gm2-body-2">
        <span class="ODSEW-ShBeI-text">Test review</span>
        <span class="ODSEW-ShBeI-H1e3jb" aria-label="Rating 4.0"></span>
        <span class="ODSEW-ShBeI-RgZmSc-date">2024-01-01</span>
    </div>
    '''
    parser = ReviewParser()
    
    # Симулируем устаревший элемент
    with patch('bs4.element.Tag.find') as mock_find:
        mock_find.side_effect = StaleElementReferenceException()
        reviews = parser.parse_reviews('test_url')
        
    assert isinstance(reviews, list)
    assert len(reviews) == 0

def test_parser_retries_on_failure(mock_driver):
    # Симулируем успех после двух неудачных попыток
    mock_driver.get.side_effect = [
        TimeoutException(),
        WebDriverException(),
        None  # Успешная попытка
    ]
    
    parser = ReviewParser(max_retries=3)
    reviews = parser.parse_reviews('test_url')
    
    assert isinstance(reviews, list)
    assert mock_driver.get.call_count == 3

def test_parser_cleans_up_driver():
    with patch('src.parser.webdriver.Chrome') as mock_chrome:
        driver = Mock()
        mock_chrome.return_value = driver
        
        parser = ReviewParser()
        del parser
        
        driver.quit.assert_called_once()

def test_parser_handles_driver_cleanup_error():
    with patch('src.parser.webdriver.Chrome') as mock_chrome:
        driver = Mock()
        driver.quit.side_effect = Exception("Cleanup error")
        mock_chrome.return_value = driver
        
        parser = ReviewParser()
        del parser  # Не должно вызвать исключение
        
        driver.quit.assert_called_once()