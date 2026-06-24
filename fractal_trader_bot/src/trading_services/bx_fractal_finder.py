# bx_fractal.py
import requests
from typing import Optional, Dict, List, Tuple


class FractalFinder:
    """
    Класс для поиска фракталов на графике
    Фрактал - экстремум среди 5 свечей (2 слева и 2 справа не превышают его)
    """
    
    def __init__(self, timeframe: str = "15m", lookback: int = 200):
        """
        Args:
            timeframe: таймфрейм для поиска фракталов (по умолчанию 15m)
            lookback: количество свечей для анализа
        """
        self.timeframe = timeframe
        self.lookback = lookback
    
    def get_klines(self, symbol: str) -> Optional[List[Dict]]:
        """Получает свечи с BingX"""
        try:
            url = "https://open-api.bingx.com/openApi/swap/v3/quote/klines"
            params = {
                'symbol': symbol,
                'interval': self.timeframe,
                'limit': self.lookback
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data'):
                    candles = []
                    for item in data['data']:
                        if isinstance(item, dict):
                            time_val = item.get('t', item.get('time', 0))
                            candles.append({
                                'high': float(item['high']),
                                'low': float(item['low']),
                                'close': float(item['close']),
                                'time': time_val
                            })

                        elif isinstance(item, list) and len(item) >= 5:
                            candles.append({
                                'high': float(item[2]),
                                'low': float(item[3]),
                                'close': float(item[4]),
                                'time': item[0]
                            })
                    if candles:
                        candles.sort(key=lambda x: x['time'])
                        return candles    
        except Exception as e:
            print(f"   ⚠️ Ошибка получения свечей {symbol}: {e}")
        return None
    
    def find_fractals(self, symbol: str) -> Dict[str, List[float]]:
        """
        Находит фракталы на графике
        
        Returns:
            {
                'up_fractals': [цена1, цена2, ...],   # верхние фракталы (high)
                'down_fractals': [цена1, цена2, ...]  # нижние фракталы (low)
            }
        """
        klines = self.get_klines(symbol)
        if not klines or len(klines) < 5:
            print(f"   ⚠️ Недостаточно данных для {symbol}")
            return {'up_fractals': [], 'down_fractals': []}
        
        up_fractals = []   # верхние фракталы (high)
        down_fractals = [] # нижние фракталы (low)
        
        # Ищем фракталы (нужно 2 свечи слева и 2 справа)
        for i in range(2, len(klines) - 2):
            # Верхний фрактал: текущий high выше всех соседних
            is_up_fractal = True
            for j in range(-2, 3):
                if j == 0:
                    continue
                if klines[i]['high'] <= klines[i + j]['high']:
                    is_up_fractal = False
                    break
            
            if is_up_fractal:
                up_fractals.append(klines[i]['high'])
            
            # Нижний фрактал: текущий low ниже всех соседних
            is_down_fractal = True
            for j in range(-2, 3):
                if j == 0:
                    continue
                if klines[i]['low'] >= klines[i + j]['low']:
                    is_down_fractal = False
                    break
            
            if is_down_fractal:
                down_fractals.append(klines[i]['low'])
        
        return {
            'up_fractals': up_fractals,
            'down_fractals': down_fractals
        }
    
    def get_nearest_fractal(self, symbol: str, current_price: float, side: str) -> Optional[float]:
        fractals = self.find_fractals(symbol)
        
        if side == "BUY":
            down_fractals = fractals['down_fractals']
            if not down_fractals:
                return None
            # Последний нижний фрактал (самый свежий)
            return down_fractals[-1]
        
        else:  # SELL
            up_fractals = fractals['up_fractals']
            if not up_fractals:
                return None
            # Последний верхний фрактал (самый свежий)
            return up_fractals[-1]
    
    def get_fractal_stop_with_buffer(self, symbol: str, current_price: float, side: str, buffer_pct: float = 0.05) -> Optional[float]:
        """
        Находит фрактал для стопа с буфером
        
        Args:
            symbol: монета
            current_price: текущая цена
            side: 'BUY' или 'SELL'
            buffer_pct: буфер в процентах от фрактала
        
        Returns:
            цена стопа (фрактал +/- буфер)
        """
        fractal = self.get_nearest_fractal(symbol, current_price, side)
        
        if fractal is None:
            return None
        
        buffer = fractal * (buffer_pct / 100)
        
        if side == "BUY":
            # Стоп чуть ниже фрактала
            return round(fractal - buffer, 4)
        else:
            # Стоп чуть выше фрактала
            return round(fractal + buffer, 4)