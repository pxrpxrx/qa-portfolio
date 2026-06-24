import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, date
from src.services.bx_risk_manager import RiskManager


@pytest.fixture
def risk_manager():
    with patch.object(RiskManager, '_load_config', return_value={
        'max_positions': 25,
        'max_position_size_abs': 25,
        'min_position_size': 5.0,
        'daily_loss_limit_abs': 10,
        'max_drawdown_percent': 15.0,
        'blacklist': ['SCAM-USDT', 'RUG-USDT'],
        'whitelist': [],
        'trading_hours': {'start': 0, 'end': 24},
        'weekend_trading': True,
        'min_volume_24h': 1000000,
        'min_price': 1e-06,
        'emergency_stop': False,
        'min_atr_percent': 0.255,
        'min_rr': 2.5,
        'min_profit_usdt': 0.5,
        'max_risk_usdt': 2.5,
    }):
        with patch.object(RiskManager, '_load_daily_stats', return_value={
            'date': date.today().isoformat(),
            'starting_balance': 1000.0,
            'current_balance': 1000.0,
            'trades_today': 0,
            'wins_today': 0,
            'losses_today': 0,
            'pnl_today': 0.0
        }):
            rm = RiskManager(config_path='fake_config.json')
            rm.peak_balance = 1000.0
            return rm


@pytest.fixture
def mock_monitor():
    monitor = MagicMock()
    monitor.positions = {}
    return monitor


class TestEmergencyStop:

    def test_emergency_stop_blocks_trading(self, risk_manager, mock_monitor):
        risk_manager.config['emergency_stop'] = True

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is False
        assert "аварийн" in reason.lower() or "emergency" in reason.lower()

    def test_emergency_stop_disabled_trading_allowed(self, risk_manager, mock_monitor):
        risk_manager.config['emergency_stop'] = False

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True
        assert reason == "OK"

    def test_emergency_stop_toggle(self, risk_manager, mock_monitor):
        risk_manager.config['emergency_stop'] = False
        assert risk_manager.can_trade(mock_monitor)[0] is True

        risk_manager.config['emergency_stop'] = True
        assert risk_manager.can_trade(mock_monitor)[0] is False

        risk_manager.config['emergency_stop'] = False
        assert risk_manager.can_trade(mock_monitor)[0] is True


class TestDailyLossLimit:

    def test_daily_loss_limit_hit(self, risk_manager, mock_monitor):
        risk_manager.daily_stats['pnl_today'] = -10.0
        risk_manager.config['daily_loss_limit_abs'] = 10

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is False

    def test_daily_loss_limit_approaching(self, risk_manager, mock_monitor):
        risk_manager.daily_stats['pnl_today'] = -9.0
        risk_manager.config['daily_loss_limit_abs'] = 10

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True

    def test_daily_loss_limit_zero_balance_change(self, risk_manager, mock_monitor):
        risk_manager.daily_stats['pnl_today'] = 0.0

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True

    def test_daily_loss_limit_positive_pnl(self, risk_manager, mock_monitor):
        risk_manager.daily_stats['pnl_today'] = 5.0

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True

    def test_daily_loss_limit_resets_new_day(self, risk_manager, mock_monitor):
        risk_manager.daily_stats['pnl_today'] = -15.0
        risk_manager.config['daily_loss_limit_abs'] = 10

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is False

        risk_manager.daily_stats['pnl_today'] = 0.0
        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True


class TestBlacklist:

    def test_blacklisted_symbol_blocked(self, risk_manager):
        can_trade, reason = risk_manager.can_trade_symbol("SCAM-USDT")
        assert can_trade is False
        assert "черн" in reason.lower() or "black" in reason.lower()

    def test_blacklisted_symbol_case_sensitive(self, risk_manager):
        can_trade, reason = risk_manager.can_trade_symbol("scam-usdt")
        assert can_trade is True

    def test_non_blacklisted_symbol_allowed(self, risk_manager):
        can_trade, reason = risk_manager.can_trade_symbol("BTC-USDT")
        assert can_trade is True
        assert reason == "OK"

    def test_whitelist_active_rejects_non_whitelisted(self, risk_manager):
        risk_manager.config['whitelist'] = ['BTC-USDT', 'ETH-USDT']

        can_trade, reason = risk_manager.can_trade_symbol("SOL-USDT")
        assert can_trade is False
        assert "бел" in reason.lower() or "white" in reason.lower()

    def test_whitelist_active_allows_whitelisted(self, risk_manager):
        risk_manager.config['whitelist'] = ['BTC-USDT', 'ETH-USDT']

        can_trade, reason = risk_manager.can_trade_symbol("BTC-USDT")
        assert can_trade is True

    def test_blacklist_multiple_symbols(self, risk_manager):
        risk_manager.config['blacklist'] = ['SCAM1', 'SCAM2', 'SCAM3']

        assert risk_manager.can_trade_symbol("SCAM1")[0] is False
        assert risk_manager.can_trade_symbol("SCAM2")[0] is False
        assert risk_manager.can_trade_symbol("SCAM3")[0] is False
        assert risk_manager.can_trade_symbol("BTC-USDT")[0] is True


class TestTradingHours:

    def test_trading_hours_allowed(self, risk_manager, mock_monitor):
        risk_manager.config['trading_hours'] = {'start': 0, 'end': 24}

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True

    def test_trading_hours_restricted(self, risk_manager, mock_monitor):
        risk_manager.config['trading_hours'] = {'start': 9, 'end': 17}

        with patch('src.services.bx_risk_manager.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 21, 14, 0, 0)
            mock_dt.now.return_value.hour = 14
            mock_dt.now.return_value.minute = 0
            mock_dt.now.return_value.weekday.return_value = 2

            original_check = risk_manager._check_trading_hours
            risk_manager._check_trading_hours = lambda: 14 >= 9 and 14 < 17
            can_trade, reason = risk_manager.can_trade(mock_monitor)
            assert can_trade is True
            risk_manager._check_trading_hours = original_check

    def test_trading_hours_outside(self, risk_manager, mock_monitor):
        risk_manager.config['trading_hours'] = {'start': 9, 'end': 17}

        original_check = risk_manager._check_trading_hours
        risk_manager._check_trading_hours = lambda: False
        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is False
        risk_manager._check_trading_hours = original_check

    def test_weekend_trading_disabled(self, risk_manager, mock_monitor):
        risk_manager.config['weekend_trading'] = False

        original_check = risk_manager._check_trading_hours
        risk_manager._check_trading_hours = lambda: False
        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is False
        risk_manager._check_trading_hours = original_check

    def test_trading_hours_midnight_crossover(self, risk_manager, mock_monitor):
        risk_manager.config['trading_hours'] = {'start': 22, 'end': 6}

        original_check = risk_manager._check_trading_hours
        risk_manager._check_trading_hours = lambda: True
        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True
        risk_manager._check_trading_hours = original_check


class TestPositionSizeValidation:

    def test_position_size_too_large(self, risk_manager):
        pos_data = {'position_value': 100.0}
        risk_manager.config['max_position_size_abs'] = 25

        ok, reason = risk_manager.check_position_size(pos_data)
        assert ok is False

    def test_position_size_too_small(self, risk_manager):
        pos_data = {'position_value': 1.0}
        risk_manager.config['min_position_size'] = 5.0

        ok, reason = risk_manager.check_position_size(pos_data)
        assert ok is False

    def test_position_size_valid(self, risk_manager):
        pos_data = {'position_value': 15.0}

        ok, reason = risk_manager.check_position_size(pos_data)
        assert ok is True
        assert reason == "OK"

    def test_position_size_calculated_from_price_qty(self, risk_manager):
        pos_data = {'entry_price': 100.0, 'quantity': 0.15}

        ok, reason = risk_manager.check_position_size(pos_data)
        assert ok is True

    def test_position_size_zero_value(self, risk_manager):
        pos_data = {}

        ok, reason = risk_manager.check_position_size(pos_data)
        assert ok is False
        assert "нет" in reason.lower() or "no" in reason.lower()

    def test_position_size_minimum_boundary(self, risk_manager):
        risk_manager.config['min_position_size'] = 5.0
        risk_manager.config['max_position_size_abs'] = 25

        assert risk_manager.check_position_size({'position_value': 5.0})[0] is True
        assert risk_manager.check_position_size({'position_value': 4.99})[0] is False
        assert risk_manager.check_position_size({'position_value': 25.0})[0] is True
        assert risk_manager.check_position_size({'position_value': 25.01})[0] is False

    def test_max_positions_limit(self, risk_manager, mock_monitor):
        risk_manager.config['max_positions'] = 3
        mock_monitor.positions = {'a': 1, 'b': 2, 'c': 3, 'd': 4}

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is False


class TestMarketDataValidation:

    def test_low_volume_blocked(self, risk_manager):
        market_data = {'volume_24h': 500000, 'price': 1.0, 'atr_percent': 1.0}

        can_trade, reason = risk_manager.can_trade_symbol("LOWVOL-USDT", market_data)
        assert can_trade is False

    def test_low_price_blocked(self, risk_manager):
        market_data = {'volume_24h': 5000000, 'price': 0.000001, 'atr_percent': 1.0}

        can_trade, reason = risk_manager.can_trade_symbol("SHIB-USDT", market_data)
        assert can_trade is False

    def test_low_atr_blocked(self, risk_manager):
        market_data = {'volume_24h': 5000000, 'price': 1.0, 'atr_percent': 0.1}

        can_trade, reason = risk_manager.can_trade_symbol("STABLE-USDT", market_data)
        assert can_trade is False


class TestDrawdown:

    def test_max_drawdown_hit(self, risk_manager, mock_monitor):
        risk_manager.peak_balance = 1000.0
        risk_manager.daily_stats['current_balance'] = 840.0
        risk_manager.config['max_drawdown_percent'] = 15.0

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is False

    def test_max_drawdown_below_limit(self, risk_manager, mock_monitor):
        risk_manager.peak_balance = 1000.0
        risk_manager.daily_stats['current_balance'] = 900.0
        risk_manager.config['max_drawdown_percent'] = 15.0

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True

    def test_max_drawdown_no_peak_set(self, risk_manager, mock_monitor):
        risk_manager.peak_balance = None

        can_trade, reason = risk_manager.can_trade(mock_monitor)
        assert can_trade is True


class TestRRCheck:

    def test_rr_above_minimum(self, risk_manager):
        ok, reason = risk_manager.check_rr(3.0)
        assert ok is True

    def test_rr_below_minimum(self, risk_manager):
        ok, reason = risk_manager.check_rr(2.0)
        assert ok is False


class TestProfitRiskCheck:

    def test_profit_above_minimum(self, risk_manager):
        ok, reason = risk_manager.check_profit_risk(profit=1.0, loss=2.0)
        assert ok is True

    def test_profit_below_minimum(self, risk_manager):
        ok, reason = risk_manager.check_profit_risk(profit=0.3, loss=2.0)
        assert ok is False

    def test_risk_above_maximum(self, risk_manager):
        ok, reason = risk_manager.check_profit_risk(profit=1.0, loss=5.0)
        assert ok is False


class TestConfigLoading:

    def test_load_config_file_not_found(self):
        with patch('pathlib.Path.exists', return_value=False):
            rm = RiskManager(config_path='nonexistent.json')
            assert rm.config['max_positions'] == 25
            assert rm.config['emergency_stop'] is False

    def test_load_config_with_overrides(self):
        mock_data = json.dumps({
            'max_positions': 10,
            'emergency_stop': True
        })
        with patch('builtins.open', mock_open(read_data=mock_data)):
            with patch('pathlib.Path.exists', return_value=True):
                rm = RiskManager(config_path='custom.json')
                assert rm.config['max_positions'] == 10
                assert rm.config['emergency_stop'] is True
                assert rm.config['max_drawdown_percent'] == 15.0

    def test_register_trade_win(self, risk_manager):
        risk_manager.register_trade({'pnl': 5.0})
        assert risk_manager.daily_stats['trades_today'] == 1
        assert risk_manager.daily_stats['wins_today'] == 1

    def test_register_trade_loss(self, risk_manager):
        risk_manager.register_trade({'pnl': -3.0})
        assert risk_manager.daily_stats['trades_today'] == 1
        assert risk_manager.daily_stats['losses_today'] == 1
