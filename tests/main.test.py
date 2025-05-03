import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import json
from src.parser import Review, NetworkError, ParsingError
from src.security import SecurityManager, SecurityError, ValidationError
from main import load_config, load_cache, save_cache

@pytest.fixture
def mock_security_manager():
    manager = Mock(spec=SecurityManager)
    manager.validate_url.return_value = True
    manager.validate_telegram_token.return_value = True
    manager.validate_chat_id.return_value = True
    manager.validate_review.return_value = True
    manager.sanitize_text.side_effect = lambda x: x
    manager.hash_data.side_effect = lambda x: f"hashed_{x}"
    return manager

@pytest.fixture
def valid_config():
    return {
        'google_maps_url': 'https://maps.google.com/place',
        'telegram_token': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
        'chat_id': '123456789'
    }

def test_load_config_success(mock_security_manager, valid_config, tmp_path):
    config_file = tmp_path / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(valid_config, f)
    
    mock_security_manager.load_secure_config.return_value = valid_config
    
    result = load_config(mock_security_manager)
    assert result == valid_config
    mock_security_manager.validate_url.assert_called_once_with(valid_config['google_maps_url'])
    mock_security_manager.validate_telegram_token.assert_called_once_with(valid_config['telegram_token'])
    mock_security_manager.validate_chat_id.assert_called_once_with(valid_config['chat_id'])

def test_load_config_invalid_url(mock_security_manager, valid_config):
    mock_security_manager.load_secure_config.return_value = valid_config
    mock_security_manager.validate_url.return_value = False
    
    with pytest.raises(ValidationError, match='Invalid Google Maps URL'):
        load_config(mock_security_manager)

def test_load_config_invalid_token(mock_security_manager, valid_config):
    mock_security_manager.load_secure_config.return_value = valid_config
    mock_security_manager.validate_telegram_token.return_value = False
    
    with pytest.raises(ValidationError, match='Invalid Telegram token'):
        load_config(mock_security_manager)

def test_load_config_invalid_chat_id(mock_security_manager, valid_config):
    mock_security_manager.load_secure_config.return_value = valid_config
    mock_security_manager.validate_chat_id.return_value = False
    
    with pytest.raises(ValidationError, match='Invalid chat ID'):
        load_config(mock_security_manager)

def test_load_cache_success(mock_security_manager, tmp_path):
    cache_file = tmp_path / 'reviews_cache.json'
    cache_data = ['review1', 'review2']
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f)
    
    result = load_cache(mock_security_manager)
    assert result == set(cache_data)

def test_load_cache_invalid_format(mock_security_manager, tmp_path):
    cache_file = tmp_path / 'reviews_cache.json'
    with open(cache_file, 'w') as f:
        json.dump('invalid_cache', f)
    
    with pytest.raises(ValidationError, match='Invalid cache format'):
        load_cache(mock_security_manager)

def test_save_cache_success(mock_security_manager, tmp_path):
    processed_reviews = {'review1', 'review2'}
    cache_file = tmp_path / 'reviews_cache.json'
    
    save_cache(processed_reviews, mock_security_manager)
    
    assert cache_file.exists()
    with open(cache_file) as f:
        saved_data = json.load(f)
        assert set(saved_data) == {'hashed_review1', 'hashed_review2'}

def test_review_validation(mock_security_manager):
    review = Review(
        text="Test review",
        rating=5,
        author="Test Author",
        date="2024-01-01"
    )
    
    mock_security_manager.validate_review.return_value = False
    
    assert not mock_security_manager.validate_review(review.__dict__)
    mock_security_manager.validate_review.assert_called_once_with(review.__dict__)

def test_review_sanitization(mock_security_manager):
    review_text = "<script>alert('test')</script>Test review"
    mock_security_manager.sanitize_text.return_value = "Test review"
    
    sanitized = mock_security_manager.sanitize_text(review_text)
    assert sanitized == "Test review"
    mock_security_manager.sanitize_text.assert_called_once_with(review_text)

def test_review_hashing(mock_security_manager):
    review_text = "Test review"
    mock_security_manager.hash_data.return_value = "hashed_review"
    
    hashed = mock_security_manager.hash_data(review_text)
    assert hashed == "hashed_review"
    mock_security_manager.hash_data.assert_called_once_with(review_text) 