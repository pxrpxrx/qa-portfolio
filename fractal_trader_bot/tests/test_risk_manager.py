import pytest
import json
from datetime import datetime

from bx_risk_manager import RiskManager


@pytest.fixture
def risk_manager(tmp_path):
    """RiskManager с временным конфигом"""
    config = {
        'max_positions': 25,
        'max_position_size_abs': 25,
        'min_position_size': 5.0,
        'daily_loss_limit_abs': 10,
        'max_drawdown_percent': 15.0,
        'blacklist': ['SCAM-USDT'],
        'whitelist': [],
        'trading_hours': {'start': 0, 'end': 24},
        'weekend_trading': True,
        'min_atr_percent': 0.255,
        'min_volume_24h': 1000000,
        'min_price': 1e-06,
        'emergency_stop': False,
        'min_rr': 2.5,
    }
    config_path = tmp_path / 'risk_config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f)
    rm = RiskManager(str(config_path))
    rm.daily_stats['pnl_today'] = 0.0
    rm.peak_balance = 1000.0
    return rm


@pytest.fixture
def mock_monitor():
    """Заглушка монитора с пустыми позициями"""
    class MockMonitor:
        positions = {}
    return MockMonitor()


class TestRiskManager:

    def test_emergency_stop_blocks_trading(self, risk_manager, mock_monitor):
        """Аварийная остановка блокирует торговлю"""
        risk_manager.config['emergency_stop'] = True
        can, reason = risk_manager.can_trade(mock_monitor)
        assert not can
        assert 'аварийн' in reason.lower()

    def test_daily_loss_limit(self, risk_manager, mock_monitor):
        """Дневной лимит убытка блокирует торговлю"""
        risk_manager.daily_stats['pnl_today'] = -15.0
        can, reason = risk_manager.can_trade(mock_monitor)
        assert not can
        assert 'дневн' in reason.lower() or 'лимит' in reason.lower()

    def test_blacklist_check(self, risk_manager):
        """Проверка чёрного списка"""
        can, reason = risk_manager.can_trade_symbol('SCAM-USDT')
        assert not can
        assert 'черн' in reason.lower()

    def test_trading_hours(self, risk_manager, mock_monitor):
        """Проверка торговых часов"""
        risk_manager.config['trading_hours'] = {'start': 23, 'end': 1}
        current_hour = datetime.now().hour
        can, reason = risk_manager.can_trade(mock_monitor)
        if current_hour >= 23 or current_hour < 1:
            assert can
        else:
            assert not can
            assert 'час' in reason.lower()

    def test_position_size_validation(self, risk_manager):
        """Валидация размера позиции"""
        ok, reason = risk_manager.check_position_size({
            'position_value': 15.0,
        })
        assert ok

        ok, reason = risk_manager.check_position_size({
            'position_value': 50.0,
        })
        assert not ok

        ok, reason = risk_manager.check_position_size({
            'position_value': 1.0,
        })
        assert not ok

    def test_rr_check(self, risk_manager):
        """Проверка R/R"""
        ok, reason = risk_manager.check_rr(3.0)
        assert ok

        ok, reason = risk_manager.check_rr(1.5)
        assert not ok
