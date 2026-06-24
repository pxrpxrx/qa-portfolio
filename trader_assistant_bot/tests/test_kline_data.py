import pytest
from unittest.mock import MagicMock, patch
from src.utilities.klineData import BingXKlineData, get_klines, get_all_symbols_from_api, load_symbols_from_file


@pytest.fixture
def kline_client():
    return BingXKlineData(testnet=True)


@pytest.fixture
def mock_list_klines():
    return [
        [1700000000000, 50000.0, 50500.0, 49800.0, 50200.0, 100.5, 1700000059000, 5000000.0, 1000, 800.0, 4000000.0],
        [1700000060000, 50200.0, 50800.0, 50100.0, 50700.0, 150.2, 1700000119000, 7600000.0, 1500, 1200.0, 6000000.0],
    ]


@pytest.fixture
def mock_dict_klines():
    return [
        {'openTime': 1700000000000, 'open': 50000.0, 'high': 50500.0, 'low': 49800.0,
         'close': 50200.0, 'volume': 100.5, 'closeTime': 1700000059000,
         'quoteVolume': 5000000.0, 'trades': 1000,
         'takerBuyBaseVolume': 800.0, 'takerBuyQuoteVolume': 4000000.0},
        {'openTime': 1700000060000, 'open': 50200.0, 'high': 50800.0, 'low': 50100.0,
         'close': 50700.0, 'volume': 150.2, 'closeTime': 1700000119000,
         'quoteVolume': 7600000.0, 'trades': 1500,
         'takerBuyBaseVolume': 1200.0, 'takerBuyQuoteVolume': 6000000.0},
    ]


class TestGetKlines:

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_klines_with_mock(self, mock_request, kline_client, mock_list_klines):
        mock_request.return_value = mock_list_klines

        result = kline_client.get_klines("BTC-USDT", "5m", limit=2)

        assert result is not None
        assert len(result) == 2
        assert result[0]['open'] == 50000.0
        assert result[0]['high'] == 50500.0
        assert result[0]['low'] == 49800.0
        assert result[0]['close'] == 50200.0
        assert result[0]['volume'] == 100.5
        assert result[1]['close'] == 50700.0

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_klines_no_data(self, mock_request, kline_client):
        mock_request.return_value = None

        result = kline_client.get_klines("BTC-USDT")
        assert result is None

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_klines_empty_list(self, mock_request, kline_client):
        mock_request.return_value = []

        result = kline_client.get_klines("BTC-USDT")
        assert result is None

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_klines_single_candle(self, mock_request, kline_client):
        mock_request.return_value = [[1700000000000, 50000.0, 50500.0, 49800.0, 50200.0, 100.5]]

        result = kline_client.get_klines("BTC-USDT", limit=1)
        assert result is not None
        assert len(result) == 1

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_klines_with_limit_param(self, mock_request, kline_client, mock_list_klines):
        mock_request.return_value = mock_list_klines

        result = kline_client.get_klines("BTC-USDT", limit=100)
        assert result is not None

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_klines_different_intervals(self, mock_request, kline_client, mock_list_klines):
        mock_request.return_value = mock_list_klines

        for interval in ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]:
            result = kline_client.get_klines("BTC-USDT", interval=interval)
            assert result is not None, f"Failed for interval {interval}"

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_klines_invalid_symbol(self, mock_request, kline_client):
        mock_request.return_value = None

        result = kline_client.get_klines("INVALID")
        assert result is None


class TestGetSymbols:

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_symbols_with_mock(self, mock_request, kline_client):
        mock_request.return_value = [
            {'symbol': 'BTC-USDT'},
            {'symbol': 'ETH-USDT'},
            {'symbol': 'SOL-USDT'},
            {'symbol': 'BTC-USD'},
        ]

        symbols = kline_client.get_symbols(force_refresh=True)

        assert 'BTC-USDT' in symbols
        assert 'ETH-USDT' in symbols
        assert 'SOL-USDT' in symbols
        assert 'BTC-USD' not in symbols

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_symbols_empty(self, mock_request, kline_client):
        mock_request.return_value = []

        symbols = kline_client.get_symbols(force_refresh=True)
        assert symbols == []

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_symbols_cache(self, mock_request, kline_client):
        mock_request.return_value = [{'symbol': 'BTC-USDT'}]

        s1 = kline_client.get_symbols(force_refresh=True)
        s2 = kline_client.get_symbols(force_refresh=False)

        assert s1 == s2
        assert mock_request.call_count == 1

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_get_symbols_no_usdt_pairs(self, mock_request, kline_client):
        mock_request.return_value = [
            {'symbol': 'BTC-USD'},
            {'symbol': 'ETH-BTC'},
        ]

        symbols = kline_client.get_symbols(force_refresh=True)
        assert symbols == []


class TestParseListFormat:

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_list_format(self, mock_request, kline_client):
        mock_request.return_value = [
            [1700000000000, 50000.0, 50500.0, 49800.0, 50200.0, 100.5,
             1700000059000, 5000000.0, 1000, 800.0, 4000000.0]
        ]

        result = kline_client.get_klines("BTC-USDT")
        assert result is not None
        candle = result[0]
        assert candle['openTime'] == 1700000000000
        assert candle['open'] == 50000.0
        assert candle['high'] == 50500.0
        assert candle['low'] == 49800.0
        assert candle['close'] == 50200.0
        assert candle['volume'] == 100.5
        assert candle['closeTime'] == 1700000059000
        assert candle['quoteVolume'] == 5000000.0
        assert candle['trades'] == 1000
        assert candle['takerBuyBaseVolume'] == 800.0
        assert candle['takerBuyQuoteVolume'] == 4000000.0

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_list_format_minimal(self, mock_request, kline_client):
        mock_request.return_value = [
            [1700000000000, 50000.0, 50500.0, 49800.0, 50200.0, 100.5]
        ]

        result = kline_client.get_klines("BTC-USDT")
        assert result is not None
        assert result[0]['close'] == 50200.0

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_list_format_missing_fields(self, mock_request, kline_client):
        mock_request.return_value = [
            [1700000000000, 50000.0]
        ]

        result = kline_client.get_klines("BTC-USDT")
        assert result is None or len(result) == 0


class TestParseDictFormat:

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_dict_format(self, mock_request, kline_client, mock_dict_klines):
        mock_request.return_value = mock_dict_klines

        result = kline_client.get_klines("BTC-USDT")
        assert result is not None
        assert len(result) == 2
        assert result[0]['open'] == 50000.0
        assert result[0]['high'] == 50500.0

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_dict_format_from_candles_field(self, mock_request, kline_client, mock_dict_klines):
        mock_request.return_value = {'candles': mock_dict_klines}

        result = kline_client.get_klines("BTC-USDT")
        assert result is not None
        assert len(result) == 2

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_dict_format_from_data_field(self, mock_request, kline_client, mock_dict_klines):
        mock_request.return_value = {'data': mock_dict_klines}

        result = kline_client.get_klines("BTC-USDT")
        assert result is not None
        assert len(result) == 2

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_dict_format_from_klines_field(self, mock_request, kline_client, mock_dict_klines):
        mock_request.return_value = {'klines': mock_dict_klines}

        result = kline_client.get_klines("BTC-USDT")
        assert result is not None
        assert len(result) == 2

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_dict_format_empty_candles(self, mock_request, kline_client):
        mock_request.return_value = {'candles': []}

        result = kline_client.get_klines("BTC-USDT")
        assert result is None

    @patch('src.utilities.klineData.BingXKlineData._request')
    def test_parse_mixed_format_with_errors(self, mock_request, kline_client):
        mock_request.return_value = [
            [1700000000000, 50000.0, 50500.0, 49800.0, 50200.0, 100.5],
            {'openTime': 1700000060000, 'open': '50200', 'high': '50800', 'low': '50100',
             'close': '50700', 'volume': '150.2'},
            None,
        ]

        result = kline_client.get_klines("BTC-USDT")
        assert result is not None


class TestRequestMethod:

    @patch('requests.get')
    def test_request_success(self, mock_get, kline_client):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'code': 0, 'data': ['result']}

        result = kline_client._request('/test')
        assert result == ['result']

    @patch('requests.get')
    def test_request_http_error(self, mock_get, kline_client):
        mock_get.return_value.status_code = 500

        result = kline_client._request('/test')
        assert result is None

    @patch('requests.get')
    def test_request_api_error(self, mock_get, kline_client):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'code': 10001, 'msg': 'Invalid symbol'}

        result = kline_client._request('/test')
        assert result is None

    @patch('requests.get')
    def test_request_timeout(self, mock_get, kline_client):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Timeout")

        result = kline_client._request('/test')
        assert result is None

    @patch('requests.get')
    def test_request_retry_on_failure(self, mock_get, kline_client):
        import requests
        from unittest.mock import MagicMock
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            MagicMock(status_code=200, json=lambda: {'code': 0, 'data': ['ok']})
        ]

        result = kline_client._request('/test')
        assert result == ['ok']
        assert mock_get.call_count == 2


class TestHelperFunctions:

    @patch('src.utilities.klineData.BingXKlineData.get_klines')
    def test_get_klines_function(self, mock_get_klines):
        mock_get_klines.return_value = [{'close': 100}]

        result = get_klines("BTC-USDT", "5m", 10)
        assert result is not None
        assert result[0]['close'] == 100

    @patch('src.utilities.klineData.BingXKlineData.get_symbols')
    def test_get_all_symbols_from_api(self, mock_get_symbols):
        mock_get_symbols.return_value = ['BTC-USDT', 'ETH-USDT']

        result = get_all_symbols_from_api()
        assert result == ['BTC-USDT', 'ETH-USDT']

    @patch('src.utilities.klineData.BingXKlineData.load_symbols_from_file')
    def test_load_symbols_from_file_function(self, mock_load):
        mock_load.return_value = ['BTC-USDT']

        result = load_symbols_from_file('test.json')
        assert result == ['BTC-USDT']


class TestLoadSymbolsFromFile:

    @patch('src.utilities.klineData.Path.exists')
    @patch('builtins.open')
    def test_load_symbols_from_file_success(self, mock_open_file, mock_exists, kline_client):
        mock_exists.return_value = True
        mock_open_file.return_value.__enter__.return_value.read.return_value = \
            '{"symbols": ["BTC-USDT", "ETH-USDT"]}'

        symbols = kline_client.load_symbols_from_file('test.json')
        assert symbols == ['BTC-USDT', 'ETH-USDT']

    @patch('src.utilities.klineData.Path.exists')
    def test_load_symbols_from_file_not_found(self, mock_exists, kline_client):
        mock_exists.return_value = False

        with patch.object(kline_client, 'get_symbols', return_value=['BTC-USDT']):
            symbols = kline_client.load_symbols_from_file('missing.json')
            assert symbols == ['BTC-USDT']
