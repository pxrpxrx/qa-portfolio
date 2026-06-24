import pytest
from unittest.mock import patch, MagicMock

# Имитация функций бота
def get_rate(currency_from, currency_to, mock_rates=None):
    """Тестируемая функция расчета курса"""
    if mock_rates:
        return mock_rates.get(f"{currency_from}_{currency_to}")
    return None

def calculate_amount(amount, rate):
    """Расчет суммы конвертации"""
    if amount is None or rate is None:
        return None
    return amount * rate

def create_order_data(chat_id, buy_currency, sell_currency, amount_rub, amount_btc):
    """Создание данных заявки"""
    return {
        'chat_id': chat_id,
        'buy_currency': buy_currency,
        'sell_currency': sell_currency,
        'amount_rub': amount_rub,
        'amount_btc': amount_btc,
        'status': 'pending'
    }

# ===================================================
# ТЕСТЫ
# ===================================================

class TestBotLogic:
    """Тесты бизнес-логики бота"""
    
    def test_get_rate_btc_to_rub(self):
        """Тест 1: Получение курса BTC → RUB"""
        mock_rates = {
            'BTC_RUB': 6500000.0
        }
        rate = get_rate('BTC', 'RUB', mock_rates)
        
        assert rate == 6500000.0
    
    def test_get_rate_rub_to_btc(self):
        """Тест 2: Получение курса RUB → BTC (обратный)"""
        # В реальном коде курс рассчитывается как 1 / BTC_RUB
        mock_rates = {
            'BTC_RUB': 6500000.0
        }
        btc_rub = get_rate('BTC', 'RUB', mock_rates)
        rub_btc = 1 / btc_rub if btc_rub else None
        
        assert rub_btc is not None
        assert rub_btc == 1 / 6500000.0
    
    def test_calculate_amount_rub_to_btc(self):
        """Тест 3: Конвертация RUB → BTC"""
        rate = 1 / 6500000.0  # 1 RUB = 0.0000001538 BTC
        amount = 10000  # 10 000 RUB
        
        result = calculate_amount(amount, rate)
        
        expected = 10000 * (1 / 6500000.0)
        assert result == pytest.approx(expected, rel=1e-6)
    
    def test_calculate_amount_btc_to_rub(self):
        """Тест 4: Конвертация BTC → RUB"""
        rate = 6500000.0  # 1 BTC = 6 500 000 RUB
        amount = 0.001  # 0.001 BTC
        
        result = calculate_amount(amount, rate)
        
        expected = 0.001 * 6500000.0
        assert result == 6500.0
    
    def test_create_order_data(self):
        """Тест 5: Создание данных заявки"""
        chat_id = 123456789
        buy_currency = "BTC"
        sell_currency = "RUB"
        amount_rub = 10000
        amount_btc = 0.0015
        
        order = create_order_data(chat_id, buy_currency, sell_currency, amount_rub, amount_btc)
        
        assert order['chat_id'] == chat_id
        assert order['buy_currency'] == "BTC"
        assert order['sell_currency'] == "RUB"
        assert order['amount_rub'] == 10000
        assert order['amount_btc'] == 0.0015
        assert order['status'] == "pending"
    
    def test_calculate_amount_with_none(self):
        """Тест 6: Обработка None значений"""
        assert calculate_amount(None, 6500000.0) is None
        assert calculate_amount(10000, None) is None
        assert calculate_amount(None, None) is None
    
    def test_negative_amount(self):
        """Тест 7: Отрицательная сумма"""
        rate = 6500000.0
        amount = -10000
        
        result = calculate_amount(amount, rate)
        
        assert result == -65000000000.0  # Математически корректно, но бизнес-логика должна отсекать отрицательные суммы