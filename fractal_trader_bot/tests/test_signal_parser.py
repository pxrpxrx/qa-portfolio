import pytest

from bx_signal_parser import BingXOrderPreparer, BingXOrder


class TestBingXOrderPreparer:

    @pytest.fixture
    def preparer(self):
        return BingXOrderPreparer()

    def test_prepare_buy_signal(self, preparer, mock_signal_long):
        """Подготовка BUY (LONG) сигнала"""
        result = preparer.prepare_signals([mock_signal_long])
        assert len(result) == 1
        prepared = result[0]

        assert prepared['direction'] == 'UP'
        assert prepared['original_symbol'] == 'BTC-USDT'

        entry = prepared['entry_order']
        assert entry['side'] == 'BUY'
        assert entry['positionSide'] == 'LONG'
        assert entry['type'] == 'MARKET'
        assert float(entry['quantity']) > 0

        summary = prepared['summary']
        assert summary['entry_price'] == 50000.0
        assert summary['stop_percent'] == 0.4
        assert summary['take_percent'] == 1.0
        assert summary['risk_reward_ratio'] == 2.5

    def test_prepare_sell_signal(self, preparer, mock_signal_short):
        """Подготовка SELL (SHORT) сигнала"""
        result = preparer.prepare_signals([mock_signal_short])
        assert len(result) == 1
        prepared = result[0]

        assert prepared['direction'] == 'DOWN'
        assert prepared['original_symbol'] == 'ETH-USDT'

        entry = prepared['entry_order']
        assert entry['side'] == 'SELL'
        assert entry['positionSide'] == 'SHORT'

    def test_empty_signals(self, preparer, mock_empty_signals):
        """Пустой список сигналов возвращает пустой список"""
        result = preparer.prepare_signals(mock_empty_signals)
        assert result == []

    def test_stop_and_take_order_creation(self, preparer, mock_signal_long):
        """Создание стоп и тейк ордеров для сигнала"""
        result = preparer.prepare_signals([mock_signal_long])
        prepared = result[0]

        assert 'stop_loss_order' in prepared
        assert 'take_profit_order' in prepared

        stop = prepared['stop_loss_order']
        assert stop['type'] == 'STOP_MARKET'
        assert stop['side'] == 'SELL'
        assert stop['positionSide'] == 'LONG'
        assert float(stop['stopPrice']) == 49800.0

        take = prepared['take_profit_order']
        assert take['type'] == 'TAKE_PROFIT_MARKET'
        assert take['side'] == 'SELL'
        assert take['positionSide'] == 'LONG'
        assert float(take['stopPrice']) == 50500.0
