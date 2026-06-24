import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, date


@pytest.fixture(scope="session")
def mock_klines_data():
    """Mock kline (candlestick) data for ATR and kline tests."""
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


@pytest.fixture(scope="session")
def mock_bingx_positions():
    """Mock positions returned by BingX API."""
    return [
        {
            'symbol': 'BTC-USDT',
            'positionSide': 'LONG',
            'positionAmt': '0.001',
            'avgPrice': '50000.0',
            'markPrice': '50500.0',
            'pnlRatio': '0.01',
            'unrealizedProfit': '0.5',
            'positionValue': '50.0'
        },
        {
            'symbol': 'ETH-USDT',
            'positionSide': 'SHORT',
            'positionAmt': '-0.1',
            'avgPrice': '3000.0',
            'markPrice': '2950.0',
            'pnlRatio': '-0.02',
            'unrealizedProfit': '-15.0',
            'positionValue': '300.0'
        }
    ]


@pytest.fixture(scope="session")
def mock_balance_data():
    """Mock balance data for balance tests."""
    return [
        {'asset': 'USDT', 'equity': '1000.50', 'balance': '1000.50'},
        {'asset': 'BTC', 'equity': '0.0', 'balance': '0.0'}
    ]


@pytest.fixture(scope="session")
def mock_api_response():
    """Factory for creating mock API responses."""
    def _create_response(code=0, data=None, msg="success"):
        return {'code': code, 'data': data or {}, 'msg': msg}
    return _create_response


@pytest.fixture(scope="session")
def mock_risk_config():
    """Default risk configuration."""
    return {
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
    }


@pytest.fixture
def mock_api_client():
    """Factory for creating a fully mocked BingXAPI client."""
    def _create_client():
        client = MagicMock()
        client.base_currency = 'VST'
        client.endpoints = {
            'server_time': '/openApi/swap/v2/server/time',
            'balance': '/openApi/swap/v2/user/balance',
            'positions': '/openApi/swap/v2/user/positions',
            'order': '/openApi/swap/v2/trade/order',
            'leverage': '/openApi/swap/v2/trade/leverage',
            'ticker': '/openApi/swap/v2/quote/ticker',
            'contracts': '/openApi/swap/v2/quote/contracts',
            'openOrders': '/openApi/swap/v2/trade/openOrders',
            'cancelAllOrders': '/openApi/swap/v2/trade/allOpenOrders'
        }
        client.get_min_qty.return_value = 0.001
        return client
    return _create_client


@pytest.fixture
def mock_kline_client():
    """Factory for creating a fully mocked BingXKlineData client."""
    def _create_client():
        client = MagicMock()
        client.testnet = True
        client.base_url = "https://open-api-vst.bingx.com"
        client.endpoints = {
            'klines': '/openApi/swap/v3/quote/klines',
            'symbols': '/openApi/swap/v2/quote/contracts'
        }
        client.timeout = 10
        client.max_retries = 3
        client.retry_delay = 2
        return client
    return _create_client
