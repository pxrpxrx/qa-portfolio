import pytest
from unittest.mock import MagicMock

from bx_fractal_finder import FractalFinder


class TestFractalFinder:

    @pytest.fixture
    def finder(self):
        return FractalFinder(timeframe="15m", lookback=200)

    @pytest.fixture
    def finder_klines_only(self):
        """FractalFinder с замоканным get_klines"""
        ff = FractalFinder(timeframe="15m", lookback=200)
        return ff

    def _patch_klines(self, finder, klines_data):
        """Подмена get_klines на возврат тестовых данных"""
        finder.get_klines = MagicMock(return_value=klines_data)

    def test_up_fractal_detection(self, finder, mock_klines_up_trend):
        """Обнаружение верхнего фрактала"""
        self._patch_klines(finder, mock_klines_up_trend)
        fractals = finder.find_fractals('BTC-USDT')
        assert len(fractals['up_fractals']) > 0
        assert 115 in fractals['up_fractals']

    def test_down_fractal_detection(self, finder, mock_klines_down_trend):
        """Обнаружение нижнего фрактала"""
        self._patch_klines(finder, mock_klines_down_trend)
        fractals = finder.find_fractals('BTC-USDT')
        assert len(fractals['down_fractals']) > 0

    def test_get_nearest_fractal_buy(self, finder, mock_klines_up_trend):
        """Получение ближайшего фрактала для BUY (нижний фрактал)"""
        self._patch_klines(finder, mock_klines_up_trend)
        fractal = finder.get_nearest_fractal('BTC-USDT', current_price=120, side='BUY')
        assert fractal is not None
        assert isinstance(fractal, (int, float))

    def test_get_nearest_fractal_sell(self, finder, mock_klines_down_trend):
        """Получение ближайшего фрактала для SELL (верхний фрактал)"""
        self._patch_klines(finder, mock_klines_down_trend)
        fractal = finder.get_nearest_fractal('ETH-USDT', current_price=180, side='SELL')
        assert fractal is not None
        assert isinstance(fractal, (int, float))

    def test_insufficient_data(self, finder, mock_klines_small):
        """Недостаточно данных (<5 свечей)"""
        self._patch_klines(finder, mock_klines_small)
        fractals = finder.find_fractals('BTC-USDT')
        assert fractals['up_fractals'] == []
        assert fractals['down_fractals'] == []
