import pytest
from unittest.mock import MagicMock, patch
from src.services.bx_trader import BingXTrader


@pytest.fixture
def mock_api():
    api = MagicMock()
    api.base_currency = 'VST'
    api.endpoints = {
        'balance': '/openApi/swap/v2/user/balance',
        'positions': '/openApi/swap/v2/user/positions',
        'order': '/openApi/swap/v2/trade/order',
        'leverage': '/openApi/swap/v2/trade/leverage',
        'ticker': '/openApi/swap/v2/quote/ticker',
        'openOrders': '/openApi/swap/v2/trade/openOrders',
        'cancelAllOrders': '/openApi/swap/v2/trade/allOpenOrders'
    }
    api.get_min_qty.return_value = 0.001
    return api


@pytest.fixture
def trader(mock_api):
    return BingXTrader(api=mock_api, required_leverage=1)


class TestTraderOpenPosition:

    def test_open_position_with_stops_success(self, trader, mock_api):
        mock_api.request.side_effect = [
            {'orderId': '12345', 'symbol': 'BTC-USDT'},
            {'orderId': '67890', 'symbol': 'BTC-USDT'},
            {'orderId': '11121', 'symbol': 'BTC-USDT'},
        ]

        with patch.object(trader, 'get_current_price', return_value=50000.0):
            with patch.object(trader, '_check_leverage', return_value=(True, "OK")):
                result = trader.open_position_with_stops(
                    symbol="BTC-USDT",
                    side="BUY",
                    quantity=0.001,
                    stop_loss_price=49000.0,
                    take_profit_price=51000.0
                )

        assert result is not None
        assert result['symbol'] == 'BTC-USDT'
        assert result['side'] == 'BUY'
        assert result['quantity'] == 0.001
        assert result['stop_loss'] == 49000.0
        assert result['take_profit'] == 51000.0
        assert result['status'] == 'OPEN'

    def test_open_position_short(self, trader, mock_api):
        mock_api.request.side_effect = [
            {'orderId': '12345', 'symbol': 'ETH-USDT'},
            {'orderId': '67890', 'symbol': 'ETH-USDT'},
            {'orderId': '11121', 'symbol': 'ETH-USDT'},
        ]

        with patch.object(trader, 'get_current_price', return_value=3000.0):
            with patch.object(trader, '_check_leverage', return_value=(True, "OK")):
                result = trader.open_position_with_stops(
                    symbol="ETH-USDT",
                    side="SELL",
                    quantity=0.1,
                    stop_loss_price=3100.0,
                    take_profit_price=2900.0
                )

        assert result is not None
        assert result['side'] == 'SELL'
        assert result['stop_loss'] == 3100.0

    def test_open_position_leverage_check_failure(self, trader, mock_api):
        with patch.object(trader, '_check_leverage', return_value=(False, "Leverage error")):
            result = trader.open_position_with_stops(
                symbol="BTC-USDT",
                side="BUY",
                quantity=0.001,
                stop_loss_price=49000.0,
                take_profit_price=51000.0
            )

        assert result is None

    def test_open_position_quantity_adjusted(self, trader, mock_api):
        mock_api.get_min_qty.return_value = 0.01

        with patch.object(trader, 'get_current_price', return_value=50000.0):
            with patch.object(trader, '_check_leverage', return_value=(True, "OK")):
                result = trader.open_position_with_stops(
                    symbol="BTC-USDT",
                    side="BUY",
                    quantity=0.001,
                    stop_loss_price=49000.0,
                    take_profit_price=51000.0
                )

        assert result is not None
        assert result['quantity'] == 0.01

    def test_open_position_api_error(self, trader, mock_api):
        mock_api.request.side_effect = Exception("API error")

        with patch.object(trader, 'get_current_price', return_value=50000.0):
            with patch.object(trader, '_check_leverage', return_value=(True, "OK")):
                result = trader.open_position_with_stops(
                    symbol="BTC-USDT",
                    side="BUY",
                    quantity=0.001,
                    stop_loss_price=49000.0,
                    take_profit_price=51000.0
                )

        assert result is None

    def test_open_position_zero_price(self, trader, mock_api):
        with patch.object(trader, 'get_current_price', return_value=0):
            result = trader.open_position_with_stops(
                symbol="BTC-USDT",
                side="BUY",
                quantity=0.001,
                stop_loss_price=49000.0,
                take_profit_price=51000.0
            )

        assert result is None

    def test_open_position_with_risk_manager_blocked(self, trader, mock_api):
        risk_manager = MagicMock()
        risk_manager.can_trade_symbol.return_value = (False, "Blacklisted")
        trader.risk_manager = risk_manager

        result = trader.open_position_with_stops(
            symbol="SCAM-USDT",
            side="BUY",
            quantity=0.001,
            stop_loss_price=0.5,
            take_profit_price=1.0
        )

        assert result is None
        risk_manager.can_trade_symbol.assert_called_once()


class TestTraderClosePosition:

    def test_close_position_success(self, trader, mock_api):
        mock_api.request.side_effect = [
            [{'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001'}],
            None,
            {'orderId': 'close123'}
        ]

        result = trader.close_position("BTC-USDT")
        assert result is True

    def test_close_position_not_found(self, trader, mock_api):
        mock_api.request.return_value = []

        result = trader.close_position("BTC-USDT")
        assert result is False

    def test_close_position_api_error(self, trader, mock_api):
        mock_api.request.side_effect = Exception("API error")

        result = trader.close_position("BTC-USDT")
        assert result is False


class TestTraderBalance:

    def test_get_balance_list_format(self, trader, mock_api):
        mock_api.request.return_value = [
            {'asset': 'USDT', 'equity': '1000.50'}
        ]

        balance = trader.get_balance(force_refresh=True)
        assert balance == 1000.50

    def test_get_balance_empty_list(self, trader, mock_api):
        mock_api.request.return_value = []

        balance = trader.get_balance(force_refresh=True)
        assert balance == 0.0

    def test_get_balance_dict_format(self, trader, mock_api):
        mock_api.request.return_value = {
            'balance': {'equity': '500.25'}
        }

        balance = trader.get_balance(force_refresh=True)
        assert balance == 500.25

    def test_get_balance_api_error(self, trader, mock_api):
        mock_api.request.side_effect = Exception("API error")

        balance = trader.get_balance(force_refresh=True)
        assert balance == 0.0

    def test_get_balance_cache(self, trader, mock_api):
        mock_api.request.return_value = [
            {'asset': 'USDT', 'equity': '1000.50'}
        ]

        b1 = trader.get_balance(force_refresh=True)
        b2 = trader.get_balance(force_refresh=False)
        assert b1 == b2
        assert mock_api.request.call_count == 1


class TestTraderPositions:

    def test_get_positions_list(self, trader, mock_api):
        mock_api.request.return_value = [
            {'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001'}
        ]

        positions = trader.get_positions()
        assert len(positions) == 1
        assert positions[0]['symbol'] == 'BTC-USDT'

    def test_get_positions_dict(self, trader, mock_api):
        mock_api.request.return_value = {
            'positions': [
                {'symbol': 'ETH-USDT', 'positionSide': 'SHORT', 'positionAmt': '0.1'}
            ]
        }

        positions = trader.get_positions()
        assert len(positions) == 1
        assert positions[0]['symbol'] == 'ETH-USDT'

    def test_get_positions_empty(self, trader, mock_api):
        mock_api.request.return_value = []

        positions = trader.get_positions()
        assert positions == []

    def test_get_positions_by_symbol(self, trader, mock_api):
        mock_api.request.return_value = [
            {'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001'}
        ]

        positions = trader.get_positions("BTC-USDT")
        mock_api.request.assert_called_once_with(
            'GET', trader.api.endpoints['positions'], {'symbol': 'BTC-USDT'}
        )
        assert len(positions) == 1


class TestTraderUpdateStops:

    def test_update_stops_success(self, trader, mock_api):
        mock_api.request.side_effect = [
            [{'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001'}],
            None,
            {'orderId': 'newstop'}
        ]

        result = trader.update_stops("BTC-USDT", new_stop_loss=49500.0)
        assert result is True

    def test_update_stops_position_not_found(self, trader, mock_api):
        mock_api.request.return_value = []

        result = trader.update_stops("BTC-USDT", new_stop_loss=49500.0)
        assert result is False

    def test_update_stops_with_take_profit(self, trader, mock_api):
        mock_api.request.side_effect = [
            [{'symbol': 'BTC-USDT', 'positionSide': 'LONG', 'positionAmt': '0.001'}],
            None,
            {'orderId': 'newstop'},
            None,
            {'orderId': 'newtake'}
        ]

        result = trader.update_stops(
            "BTC-USDT",
            new_stop_loss=49500.0,
            new_take_profit=51500.0
        )
        assert result is True

    def test_update_stops_api_error(self, trader, mock_api):
        mock_api.request.side_effect = Exception("API error")

        result = trader.update_stops("BTC-USDT", new_stop_loss=49500.0)
        assert result is False


class TestTraderLeverage:

    def test_check_leverage_already_correct(self, trader, mock_api):
        mock_api.request.return_value = {'longLeverage': 1}

        ok, msg = trader._check_leverage("BTC-USDT")
        assert ok is True

    def test_check_leverage_needs_update(self, trader, mock_api):
        mock_api.request.side_effect = [
            {'longLeverage': 5},
            {'msg': 'OK'},
            {'msg': 'OK'}
        ]

        ok, msg = trader._check_leverage("BTC-USDT", force=True)
        assert ok is True

    def test_check_leverage_error(self, trader, mock_api):
        mock_api.request.side_effect = Exception("API error")

        ok, msg = trader._check_leverage("BTC-USDT", force=True)
        assert ok is False
