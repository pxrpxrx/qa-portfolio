import pytest
import sys
from pathlib import Path

src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from positionSizing import positionSizing


class TestPositionSizing:

    def test_calculate_size_up_trend(self):
        """Расчёт размера позиции для LONG (UP)"""
        result = positionSizing(
            capital=5000,
            price=50000.0,
            atr=200.0,
            direction="UP",
            risk_percent=0.02,
            stop_loss_mult=1.25,
            take_profit_mult=2.5,
            target_position_usdt=5.5,
        )
        assert 'error' not in result, f"Ошибка: {result.get('error')}"
        assert result['size'] > 0
        assert result['entry'] == 50000.0
        assert result['direction'] == "UP"
        assert result['stop_loss'] < result['entry']
        assert result['take_profit'] > result['entry']
        assert result['risk_reward_ratio'] > 0

    def test_calculate_size_down_trend(self):
        """Расчёт размера позиции для SHORT (DOWN)"""
        result = positionSizing(
            capital=5000,
            price=3000.0,
            atr=60.0,
            direction="DOWN",
            risk_percent=0.02,
            stop_loss_mult=1.25,
            take_profit_mult=2.5,
            target_position_usdt=5.5,
        )
        assert 'error' not in result, f"Ошибка: {result.get('error')}"
        assert result['size'] > 0
        assert result['entry'] == 3000.0
        assert result['direction'] == "DOWN"
        assert result['stop_loss'] > result['entry']
        assert result['take_profit'] < result['entry']

    def test_minimum_stop_protection(self):
        """Проверка минимального стопа (не ниже 0.2%)"""
        tiny_atr = 1.0
        price = 50000.0
        result = positionSizing(
            capital=5000,
            price=price,
            atr=tiny_atr,
            direction="UP",
        )
        assert result['stop_percent'] >= 0.2
        assert result['take_percent'] >= 0.6

    def test_no_price_returns_error(self):
        """Если цена не передана — возвращается ошибка"""
        result = positionSizing(
            capital=5000,
            price=None,
            atr=200.0,
            direction="UP",
        )
        assert 'error' in result
        assert result['error'] == 'Нет цены'

    def test_target_position_usdt(self):
        """Проверка target_position_usdt"""
        target = 5.5
        price = 50000.0
        result = positionSizing(
            capital=5000,
            price=price,
            atr=200.0,
            direction="UP",
            target_position_usdt=target,
        )
        expected_size = target / price
        assert abs(result['size'] - expected_size) < 1e-10
        assert abs(result['position_value'] - target) < 0.01

    def test_risk_reward_ratio_calculation(self):
        """Расчёт R/R корректен"""
        result = positionSizing(
            capital=5000,
            price=50000.0,
            atr=250.0,
            direction="UP",
            stop_loss_mult=1.0,
            take_profit_mult=3.0,
        )
        rr = result['risk_reward_ratio']
        assert rr > 0
        expected_min_rr = (0.6 - 0.1) / (0.2 + 0.1)
        assert rr >= expected_min_rr * 0.5
