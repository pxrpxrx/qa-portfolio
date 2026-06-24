import pytest
from unittest.mock import patch, MagicMock
from src.utilities.bx_atr import ATR, calculate_position


@pytest.fixture
def atr():
    return ATR()


@pytest.fixture
def mock_klines():
    return [
        {'high': 105, 'low': 95, 'close': 100},
        {'high': 110, 'low': 98, 'close': 108},
        {'high': 112, 'low': 102, 'close': 110},
        {'high': 108, 'low': 100, 'close': 105},
        {'high': 115, 'low': 105, 'close': 112},
        {'high': 120, 'low': 108, 'close': 118},
        {'high': 118, 'low': 110, 'close': 115},
        {'high': 122, 'low': 112, 'close': 120},
        {'high': 125, 'low': 115, 'close': 122},
        {'high': 128, 'low': 118, 'close': 125},
        {'high': 130, 'low': 120, 'close': 128},
        {'high': 132, 'low': 122, 'close': 130},
        {'high': 135, 'low': 125, 'close': 132},
        {'high': 138, 'low': 128, 'close': 135},
        {'high': 140, 'low': 130, 'close': 138},
        {'high': 142, 'low': 132, 'close': 140},
    ]


class TestATRCalculation:

    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_calculate_atr_with_mock_data(self, mock_get_klines, atr, mock_klines):
        mock_get_klines.return_value = mock_klines

        result = atr.calculate("BTC-USDT", "1h", period=14)

        assert result is not None
        assert 'atr' in result
        assert 'atr_3' in result
        assert 'atr_percent' in result
        assert result['atr'] > 0
        assert result['atr_3'] == round(result['atr'] * 3, 8)
        assert result['atr_percent'] > 0

    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_calculate_atr_insufficient_data(self, mock_get_klines, atr):
        mock_get_klines.return_value = [
            {'high': 100, 'low': 95, 'close': 98},
            {'high': 102, 'low': 96, 'close': 100},
        ]

        result = atr.calculate("BTC-USDT", "1h", period=14)
        assert result is None

    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_calculate_atr_3x(self, mock_get_klines, atr, mock_klines):
        mock_get_klines.return_value = mock_klines

        result = atr.calculate("BTC-USDT", "1h", period=14)
        assert result is not None
        assert result['atr_3'] == round(result['atr'] * 3, 8)

    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_calculate_atr_percent(self, mock_get_klines, atr, mock_klines):
        mock_get_klines.return_value = mock_klines

        result = atr.calculate("BTC-USDT", "1h", period=14)
        assert result is not None

        last_close = mock_klines[-1]['close']
        expected_pct = round((result['atr'] / last_close) * 100, 4)
        assert result['atr_percent'] == expected_pct

    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_calculate_atr_returns_none_on_api_error(self, mock_get_klines, atr):
        mock_get_klines.return_value = None

        result = atr.calculate("BTC-USDT", "1h", period=14)
        assert result is None

    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_different_timeframes(self, mock_get_klines, atr, mock_klines):
        mock_get_klines.return_value = mock_klines

        for tf in ["15m", "1h", "4h", "1d"]:
            result = atr.calculate("BTC-USDT", tf, period=14)
            assert result is not None, f"Failed for timeframe {tf}"

    @patch('src.utilities.bx_atr.ATR.get_current_price')
    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_get_current_price(self, mock_get_klines, mock_get_price, atr):
        mock_get_price.return_value = 50000.0
        mock_get_klines.return_value = [
            {'high': 105, 'low': 95, 'close': 100},
            {'high': 110, 'low': 98, 'close': 108},
        ]

        price = atr.get_current_price("BTC-USDT")
        assert price == 50000.0

    @patch('src.utilities.bx_atr.ATR.get_current_price')
    @patch('src.utilities.bx_atr.ATR.get_klines')
    def test_get_current_price_api_error(self, mock_get_klines, mock_get_price, atr):
        mock_get_price.return_value = None
        mock_get_klines.return_value = None

        price = atr.get_current_price("BTC-USDT")
        assert price is None

    def test_calculate_position_correctly(self):
        capital = 1000.0
        risk_percent = 1.0
        stop_percent = 14.6
        entry_price = 100.0

        result = calculate_position(capital, risk_percent, stop_percent, entry_price)

        expected_risk = 10.0
        expected_position = 10.0 / 0.146
        expected_qty = expected_position / 100.0

        assert result['risk_usdt'] == expected_risk
        assert result['stop_percent'] == stop_percent
        assert abs(result['position_usdt'] - expected_position) < 0.01
        assert abs(result['quantity'] - expected_qty) < 0.0001
        assert abs(result['loss_at_stop'] - expected_risk) < 0.01
