import pytest
import requests
from unittest.mock import patch, MagicMock

# Конфигурация для тестов
API_KEY = "test_api_key"
BTC_ID = 93
RUB_ID = 105
MY_EXCHANGER_ID = 1029
BASE_URL = "https://bestchange.app/v2"

def get_bestchange_rate(from_id, to_id, exchanger_id=None):
    """Тестируемая функция (копия из кода бота)"""
    url = f"{BASE_URL}/{API_KEY}/rates/{from_id}-{to_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        rates = data.get('rates', {}).get(f"{from_id}-{to_id}", [])
        
        if not rates:
            return None
        
        if exchanger_id is not None:
            for rate in rates:
                if rate.get('changer') == exchanger_id:
                    return rate
            return rates[0]
        return rates[0]
    except Exception:
        return None

# ===================================================
# ТЕСТЫ
# ===================================================

class TestBestChangeAPI:
    """Тесты для BestChange API"""
    
    @patch('requests.get')
    def test_get_rate_success(self, mock_get):
        """Тест 1: Успешное получение курса"""
        # Подготавливаем мок-ответ
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rates": {
                "93-105": [
                    {
                        "changer": 1029,
                        "rate": 0.000016,
                        "reserve": 1000000,
                        "inmin": 500,
                        "inmax": 5000000
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Выполняем тест
        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
        
        # Проверяем результат
        assert result is not None
        assert result['changer'] == 1029
        assert result['rate'] == 0.000016
        assert result['reserve'] == 1000000
    
    @patch('requests.get')
    def test_get_rate_no_rates(self, mock_get):
        """Тест 2: API вернул пустой список курсов"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {}}
        mock_get.return_value = mock_response
        
        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
        
        assert result is None
    
    @patch('requests.get')
    def test_get_rate_timeout(self, mock_get):
        """Тест 3: Таймаут при запросе к API"""
        mock_get.side_effect = requests.exceptions.Timeout
        
        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
        
        assert result is None
    
    @patch('requests.get')
    def test_get_rate_connection_error(self, mock_get):
        """Тест 4: Ошибка подключения к API"""
        mock_get.side_effect = requests.exceptions.ConnectionError
        
        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
        
        assert result is None
    
    @patch('requests.get')
    def test_get_rate_invalid_api_key(self, mock_get):
        """Тест 5: Неверный API-ключ"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_get.return_value = mock_response
        
        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
        
        # Функция вернёт None, так как rates отсутствуют
        assert result is None