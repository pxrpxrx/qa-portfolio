"""
Тесты для BestChange API интеграции.
Импортирует реальные функции из client_bot.py
"""
import pytest
import requests
from unittest.mock import patch, MagicMock
from client_bot import get_bestchange_rate

# Тестовые константы
API_KEY = "test_api_key"
BTC_ID = 93
RUB_ID = 105
MY_EXCHANGER_ID = 1029


class TestBestChangeAPI:
    """Тесты для BestChange API"""

    @patch('client_bot.requests.get')
    def test_get_rate_success(self, mock_get):
        """Тест 1: Успешное получение курса"""
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

        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)

        assert result is not None
        assert result['exchanger_id'] == 1029
        assert result['rate'] > 0
        assert result['reserve'] == 1000000

    @patch('client_bot.requests.get')
    def test_get_rate_no_rates(self, mock_get):
        """Тест 2: API вернул пустой список курсов"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {}}
        mock_get.return_value = mock_response

        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)

        assert result is None

    @patch('client_bot.requests.get')
    def test_get_rate_timeout(self, mock_get):
        """Тест 3: Таймаут при запросе к API"""
        mock_get.side_effect = requests.exceptions.Timeout

        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)

        assert result is None

    @patch('client_bot.requests.get')
    def test_get_rate_connection_error(self, mock_get):
        """Тест 4: Ошибка подключения к API"""
        mock_get.side_effect = requests.exceptions.ConnectionError

        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)

        assert result is None

    @patch('client_bot.requests.get')
    def test_get_rate_invalid_response(self, mock_get):
        """Тест 5: Некорректный ответ API"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_get.return_value = mock_response

        result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)

        assert result is None
