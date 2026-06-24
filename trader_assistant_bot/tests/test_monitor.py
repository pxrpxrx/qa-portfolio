import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.services.bx_monitor import BxMonitor, Position


@pytest.fixture
def mock_trader():
    trader = MagicMock()
    trader.get_balance.return_value = 1000.0
    return trader


@pytest.fixture
def monitor(mock_trader):
    return BxMonitor(trader=mock_trader)


class TestAddPosition:

    def test_add_position(self, monitor):
        pos = monitor.add_position(
            symbol="BTC-USDT",
            side="BUY",
            entry_price=50000.0,
            quantity=0.001,
            stop_percent=2.5,
            take_percent=5.0
        )

        assert isinstance(pos, Position)
        assert pos.symbol == "BTC-USDT"
        assert pos.side == "BUY"
        assert pos.entry_price == 50000.0
        assert pos.quantity == 0.001
        assert pos.stop_percent == 2.5
        assert pos.take_percent == 5.0
        assert pos.status == "OPEN"
        assert "BTC-USDT" in monitor.positions

    def test_add_multiple_positions(self, monitor):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        monitor.add_position("ETH-USDT", "SELL", 3000, 0.1, 2.0, 4.0)

        assert len(monitor.positions) == 2
        assert "BTC-USDT" in monitor.positions
        assert "ETH-USDT" in monitor.positions

    def test_add_position_overwrites_existing(self, monitor):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        monitor.add_position("BTC-USDT", "SELL", 51000, 0.002, 3.0, 6.0)

        pos = monitor.positions["BTC-USDT"]
        assert pos.side == "SELL"
        assert pos.entry_price == 51000.0

    def test_add_position_stores_stop_take(self, monitor):
        pos = monitor.add_position("SOL-USDT", "BUY", 150.0, 1.0, 3.0, 7.5)

        assert pos.stop_percent == 3.0
        assert pos.take_percent == 7.5

    def test_add_position_records_entry_time(self, monitor):
        pos = monitor.add_position("ADA-USDT", "BUY", 0.5, 100, 2.0, 4.0)

        assert pos.entry_time is not None
        assert isinstance(pos.entry_time, datetime)


class TestSyncPositions:

    def test_sync_positions_empty(self, monitor, mock_trader):
        mock_trader.get_positions.return_value = []
        mock_trader.get_balance.return_value = 1000.0

        monitor.sync_positions()

        assert len(monitor.positions) == 0

    def test_sync_positions_new_position(self, monitor, mock_trader):
        mock_trader.get_positions.return_value = [
            {'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001',
             'avgPrice': '50000.0', 'markPrice': '50500.0', 'pnlRatio': '0.01'}
        ]

        with patch('src.services.bx_monitor.positionSizing') as mock_sizing:
            mock_sizing.return_value = {
                'stop_percent': 2.5,
                'take_percent': 5.0,
                'atr_pct': 1.5
            }
            monitor.sync_positions()

        assert "BTC-USDT" in monitor.positions
        pos = monitor.positions["BTC-USDT"]
        assert pos.side == "BUY"
        assert pos.stop_percent == 2.5
        assert pos.take_percent == 5.0

    def test_sync_positions_multiple_new(self, monitor, mock_trader):
        mock_trader.get_positions.return_value = [
            {'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001',
             'avgPrice': '50000', 'markPrice': '50500', 'pnlRatio': '0.01'},
            {'symbol': 'ETH-USDT', 'positionSide': 'SHORT', 'positionAmt': '-0.1',
             'avgPrice': '3000', 'markPrice': '3020', 'pnlRatio': '-0.0067'}
        ]

        with patch('src.services.bx_monitor.positionSizing') as mock_sizing:
            mock_sizing.return_value = {
                'stop_percent': 2.0, 'take_percent': 4.0, 'atr_pct': 1.2
            }
            monitor.sync_positions()

        assert len(monitor.positions) == 2

    def test_sync_positions_removes_closed(self, monitor, mock_trader):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        monitor.add_position("ETH-USDT", "SELL", 3000, 0.1, 2.0, 4.0)

        mock_trader.get_positions.return_value = [
            {'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001',
             'avgPrice': '50000', 'markPrice': '50500', 'pnlRatio': '0.01'}
        ]

        monitor.sync_positions()

        assert "BTC-USDT" in monitor.positions
        assert "ETH-USDT" not in monitor.positions

    def test_sync_positions_rate_limiting(self, monitor, mock_trader):
        mock_trader.get_positions.return_value = []

        for _ in range(10):
            monitor.sync_positions()

        assert len(monitor._api_call_timestamps) <= 100

    def test_sync_positions_api_error(self, monitor, mock_trader):
        mock_trader.get_positions.side_effect = Exception("API error")

        monitor.sync_positions()

        assert len(monitor.positions) == 0


class TestExitConditions:

    def test_exit_conditions_stop_loss_long(self, monitor):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        import time
        monitor._check_exit_conditions("BTC-USDT", -3.0)
        time.sleep(0.1)
        assert "BTC-USDT" not in monitor.positions

    def test_exit_conditions_stop_loss_short(self, monitor):
        monitor.add_position("ETH-USDT", "SELL", 3000, 0.1, 2.0, 4.0)
        import time
        monitor._check_exit_conditions("ETH-USDT", -3.0)
        time.sleep(0.1)
        assert "ETH-USDT" not in monitor.positions

    def test_exit_conditions_take_profit_long(self, monitor):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        import time
        monitor._check_exit_conditions("BTC-USDT", 6.0)
        time.sleep(0.1)
        assert "BTC-USDT" not in monitor.positions

    def test_exit_conditions_take_profit_short(self, monitor):
        monitor.add_position("ETH-USDT", "SELL", 3000, 0.1, 2.0, 4.0)
        import time
        monitor._check_exit_conditions("ETH-USDT", 5.0)
        time.sleep(0.1)

        assert "ETH-USDT" not in monitor.positions

    def test_no_exit_within_bounds(self, monitor, mock_trader):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)

        monitor._check_exit_conditions("BTC-USDT", 1.0)
        assert "BTC-USDT" in monitor.positions

    def test_exit_conditions_only_existing_position(self, monitor):
        monitor._check_exit_conditions("NONEXISTENT", -5.0)
        assert "NONEXISTENT" not in monitor.positions

    def test_exit_triggers_close_position(self, monitor, mock_trader):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        mock_trader.get_positions.return_value = [
            {'symbol': 'BTC-USDT', 'markPrice': '48000', 'unrealizedProfit': '-20'}
        ]

        monitor._check_exit_conditions("BTC-USDT", -3.0)

    def test_exit_with_orchestrator(self, monitor, mock_trader):
        orchestrator = MagicMock()
        monitor.orchestrator = orchestrator
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        mock_trader.get_positions.return_value = [
            {'symbol': 'BTC-USDT', 'markPrice': '48000', 'unrealizedProfit': '-20'}
        ]
        mock_trader.close_position.return_value = True

        monitor._check_exit_conditions("BTC-USDT", -3.0)

    def test_exit_reason_stop_loss_logged(self, monitor, mock_trader):
        monitor.add_position("SOL-USDT", "BUY", 150, 1.0, 3.0, 7.0)

        with patch('threading.Thread') as mock_thread:
            monitor._check_exit_conditions("SOL-USDT", -4.0)
            mock_thread.assert_called_once()

    def test_exit_reason_take_profit_logged(self, monitor, mock_trader):
        monitor.add_position("SOL-USDT", "BUY", 150, 1.0, 3.0, 7.0)

        with patch('threading.Thread') as mock_thread:
            monitor._check_exit_conditions("SOL-USDT", 8.0)
            mock_thread.assert_called_once()

    def test_exact_stop_loss_boundary(self, monitor):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        monitor._check_exit_conditions("BTC-USDT", -2.5)
        assert "BTC-USDT" not in monitor.positions


class TestPositionPnlCalculation:

    def test_pnl_from_pnl_ratio(self, monitor, mock_trader):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
        mock_trader.get_positions.return_value = [
            {'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001',
             'avgPrice': '50000', 'markPrice': '51000', 'pnlRatio': '0.02'}
        ]

        monitor.sync_positions()
        assert "BTC-USDT" in monitor.positions

    def test_pnl_from_unrealized_profit(self, monitor, mock_trader):
        monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 5.0, 30.0)
        mock_trader.get_positions.return_value = [
            {'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001',
             'avgPrice': '50000', 'markPrice': '51000',
             'unrealizedProfit': '10', 'positionValue': '50'}
        ]

        monitor.sync_positions()
        assert "BTC-USDT" in monitor.positions


class TestRateLimiting:

    def test_rate_limit_respects_max_calls(self, monitor):
        for _ in range(5):
            monitor._check_rate_limit()

        assert len(monitor._api_call_timestamps) == 5

    def test_rate_limit_clears_old(self, monitor):
        import time
        old_ts = time.time() - 2
        monitor._api_call_timestamps.append(old_ts)

        monitor._check_rate_limit()
        assert old_ts not in monitor._api_call_timestamps
