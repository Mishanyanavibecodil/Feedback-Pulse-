import pytest
from unittest.mock import patch, Mock
from telegram.error import TelegramError
from src.notifier import TelegramNotifier

@pytest.fixture
def mock_bot():
    with patch('src.notifier.Bot') as mock_bot_class:
        bot = Mock()
        mock_bot_class.return_value = bot
        yield bot

def test_alert_sending_success(mock_bot):
    notifier = TelegramNotifier(token='test_token', chat_id='123')
    review = {
        'text': 'Test review',
        'rating': 1.0,
        'date': '2024-01-01'
    }
    
    result = notifier.send_alert(review)
    
    assert result is True
    mock_bot.send_message.assert_called_once()
    
    # Проверяем формат сообщения
    call_args = mock_bot.send_message.call_args[1]
    assert call_args['chat_id'] == '123'
    assert 'Test review' in call_args['text']
    assert '1.0' in call_args['text']
    assert '2024-01-01' in call_args['text']

def test_alert_sending_invalid_token():
    with pytest.raises(ValueError):
        TelegramNotifier(token='', chat_id='123')

def test_alert_sending_invalid_chat_id():
    with pytest.raises(ValueError):
        TelegramNotifier(token='test_token', chat_id='')

def test_alert_sending_telegram_error(mock_bot):
    mock_bot.send_message.side_effect = TelegramError("Test error")
    notifier = TelegramNotifier(token='test_token', chat_id='123')
    
    result = notifier.send_alert({'text': 'Test', 'rating': 1.0})
    assert result is False

def test_alert_sending_invalid_review(mock_bot):
    notifier = TelegramNotifier(token='test_token', chat_id='123')
    
    # Отсутствует обязательное поле
    result = notifier.send_alert({'text': 'Test'})
    assert result is False
    mock_bot.send_message.assert_not_called()
    
    # Неверный тип данных
    result = notifier.send_alert({'text': 123, 'rating': 'invalid'})
    assert result is False
    mock_bot.send_message.assert_not_called()

def test_alert_sending_network_error(mock_bot):
    mock_bot.send_message.side_effect = Exception("Network error")
    notifier = TelegramNotifier(token='test_token', chat_id='123')
    
    result = notifier.send_alert({'text': 'Test', 'rating': 1.0})
    assert result is False