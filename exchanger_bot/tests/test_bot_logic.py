"""
Тесты бизнес-логики бота.
Импортирует реальные функции из client_bot.py
"""
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from pathlib import Path
from client_bot import get_rate, create_order, get_main_keyboard, get_buy_keyboard


class TestBotLogic:
    """Тесты бизнес-логики бота"""

    @patch('client_bot.get_btc_rub')
    def test_get_rate_btc_to_rub(self, mock_btc_rub):
        """Тест 1: Получение курса BTC → RUB"""
        mock_btc_rub.return_value = 6500000.0

        rate = get_rate('BTC', 'RUB')

        assert rate == 6500000.0
        mock_btc_rub.assert_called_once()

    @patch('client_bot.get_btc_rub')
    def test_get_rate_rub_to_btc(self, mock_btc_rub):
        """Тест 2: Получение курса RUB → BTC (обратный)"""
        mock_btc_rub.return_value = 6500000.0

        rate = get_rate('RUB', 'BTC')

        assert rate is not None
        assert rate == pytest.approx(1 / 6500000.0, rel=1e-6)

    @patch('client_bot.get_btc_rub')
    def test_get_rate_unknown_pair(self, mock_btc_rub):
        """Тест 3: Неизвестная валютная пара"""
        rate = get_rate('ETH', 'USD')

        assert rate is None

    @patch('client_bot.sqlite3.connect')
    def test_create_order(self, mock_connect):
        """Тест 4: Создание заявки"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1

        chat_id = 123456789
        buy_currency = "BTC"
        sell_currency = "RUB"
        amount_rub = 10000
        amount_btc = 0.0015

        order_id = create_order(chat_id, buy_currency, sell_currency, amount_rub, amount_btc)

        assert order_id == 1
        mock_cursor.execute.assert_called()

    def test_get_main_keyboard(self):
        """Тест 5: Главная клавиатура содержит кнопки"""
        keyboard = get_main_keyboard()

        assert keyboard is not None
        assert len(keyboard.keyboard) > 0

    def test_get_buy_keyboard(self):
        """Тест 6: Клавиатура покупки содержит валюты"""
        keyboard = get_buy_keyboard()

        assert keyboard is not None
        assert len(keyboard.keyboard) > 0

    @patch('client_bot.get_btc_rub')
    def test_calculate_amount_rub_to_btc(self, mock_btc_rub):
        """Тест 7: Конвертация RUB → BTC"""
        mock_btc_rub.return_value = 6500000.0

        rate = get_rate('RUB', 'BTC')
        amount_rub = 10000
        amount_btc = amount_rub * rate

        assert amount_btc == pytest.approx(10000 / 6500000.0, rel=1e-6)

    @patch('client_bot.get_btc_rub')
    def test_calculate_amount_btc_to_rub(self, mock_btc_rub):
        """Тест 8: Конвертация BTC → RUB"""
        mock_btc_rub.return_value = 6500000.0

        rate = get_rate('BTC', 'RUB')
        amount_btc = 0.001
        amount_rub = amount_btc * rate

        assert amount_rub == pytest.approx(6500.0, rel=1e-6)
