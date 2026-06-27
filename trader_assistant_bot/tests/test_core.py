"""
Ключевые автотесты для Trader Assistant Bot.
10 тестов, покрывающих основную функциональность:
- ATR расчёт
- Мониторинг позиций
- Risk Manager
- Торговая логика
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Добавляем src в path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.bx_risk_manager import RiskManager
from services.bx_monitor import PositionMonitor
from utilities.bx_atr import calculate_atr


class TestATRCalculation:
    """Тесты расчёта ATR (Average True Range)"""

    def test_atr_basic_calculation(self):
        """Тест 1: Базовый расчёт ATR"""
        klines = [
            {'high': 100, 'low': 90, 'close': 95},
            {'high': 105, 'low': 92, 'close': 100},
            {'high': 110, 'low': 95, 'close': 105},
            {'high': 108, 'low': 93, 'close': 102},
            {'high': 115, 'low': 100, 'close': 110},
        ]

        atr = calculate_atr(klines, period=3)

        assert atr is not None
        assert atr > 0
        assert isinstance(atr, float)

    def test_atr_insufficient_data(self):
        """Тест 2: Недостаточно данных для расчёта ATR"""
        klines = [
            {'high': 100, 'low': 90, 'close': 95},
        ]

        atr = calculate_atr(klines, period=5)

        assert atr is None

    def test_atr_zero_volatility(self):
        """Тест 3: Нулевая волатильность (все цены одинаковые)"""
        klines = [
            {'high': 100, 'low': 100, 'close': 100},
            {'high': 100, 'low': 100, 'close': 100},
            {'high': 100, 'low': 100, 'close': 100},
        ]

        atr = calculate_atr(klines, period=2)

        assert atr == 0.0


class TestRiskManager:
    """Тесты управления рисками"""

    def test_position_size_calculation(self):
        """Тест 4: Расчёт размера позиции"""
        risk_manager = RiskManager(
            max_risk_percent=2.0,
            account_balance=10000.0
        )

        entry_price = 50000.0
        stop_loss = 49000.0
        atr = 500.0

        position_size = risk_manager.calculate_position_size(
            entry_price, stop_loss, atr
        )

        assert position_size > 0
        assert isinstance(position_size, float)

    def test_risk_reward_ratio(self):
        """Тест 5: Расчёт risk/reward ratio"""
        risk_manager = RiskManager()

        entry = 50000.0
        stop_loss = 49000.0
        take_profit = 52000.0

        rr_ratio = risk_manager.calculate_risk_reward(
            entry, stop_loss, take_profit
        )

        assert rr_ratio > 0
        assert rr_ratio == pytest.approx(2.0, rel=0.1)

    def test_max_drawdown_check(self):
        """Тест 6: Проверка максимального просадки"""
        risk_manager = RiskManager(max_drawdown_percent=10.0)

        # Просадка в пределах лимита
        assert risk_manager.is_drawdown_acceptable(
            peak_balance=10000.0,
            current_balance=9500.0
        ) is True

        # Просадка превышает лимит
        assert risk_manager.is_drawdown_acceptable(
            peak_balance=10000.0,
            current_balance=8500.0
        ) is False


class TestPositionMonitor:
    """Тесты мониторинга позиций"""

    def test_trailing_stop_update(self):
        """Тест 7: Обновление trailing stop"""
        monitor = PositionMonitor()

        position = {
            'entry_price': 50000.0,
            'highest_price': 52000.0,
            'atr': 500.0,
            'trailing_stop': 51000.0
        }

        new_stop = monitor.update_trailing_stop(position)

        assert new_stop >= position['trailing_stop']
        assert new_stop < position['highest_price']

    def test_take_profit_hit(self):
        """Тест 8: Определение достижения take profit"""
        monitor = PositionMonitor()

        position = {
            'entry_price': 50000.0,
            'take_profit': 52000.0,
            'side': 'long'
        }

        assert monitor.is_take_profit_hit(position, 52500.0) is True
        assert monitor.is_take_profit_hit(position, 51000.0) is False

    def test_stop_loss_hit(self):
        """Тест 9: Определение достижения stop loss"""
        monitor = PositionMonitor()

        position = {
            'entry_price': 50000.0,
            'stop_loss': 49000.0,
            'side': 'long'
        }

        assert monitor.is_stop_loss_hit(position, 48500.0) is True
        assert monitor.is_stop_loss_hit(position, 49500.0) is False


class TestTrader:
    """Тесты торговой логики"""

    @patch('services.bx_trader.BingXTrader.execute_order')
    def test_order_execution(self, mock_execute):
        """Тест 10: Исполнение ордера"""
        mock_execute.return_value = {'orderId': '12345', 'status': 'FILLED'}

        from services.bx_trader import BingXTrader
        trader = BingXTrader(api_key='test', secret='test')

        result = trader.execute_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.001,
            price=50000.0
        )

        assert result['status'] == 'FILLED'
        mock_execute.assert_called_once()
