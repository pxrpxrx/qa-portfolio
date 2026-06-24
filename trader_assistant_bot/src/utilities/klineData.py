# klineData.py
import requests
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class BingXKlineData:
    """
    Класс для получения свечных данных с BingX
    """
    
    def __init__(self, testnet: bool = True):
        """
        Инициализация
        
        Args:
            testnet: True для тестовой сети, False для реальной
        """
        self.testnet = testnet
        
        # Базовые URL для API
        if testnet:
            self.base_url = "https://open-api-vst.bingx.com"
        else:
            self.base_url = "https://open-api.bingx.com"
        
        # Эндпоинты
        self.endpoints = {
            'klines': '/openApi/swap/v3/quote/klines',
            'symbols': '/openApi/swap/v2/quote/contracts'
        }
        
        # Кэш для символов
        self._symbols_cache = None
        self._symbols_cache_time = 0
        
        # Настройки
        self.timeout = 10
        self.max_retries = 3
        self.retry_delay = 2
        
        logger.info(f"BingX Kline Data инициализирован (тестнет: {testnet})")
    
    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Выполнение запроса к API
        
        Args:
            endpoint: эндпоинт API
            params: параметры запроса
        
        Returns:
            ответ API или None при ошибке
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        return data.get('data')
                    else:
                        logger.warning(f"API ошибка: {data.get('msg')}")
                else:
                    logger.warning(f"HTTP ошибка: {response.status_code}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Запрос ошибка (попытка {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        return None
    
    def get_symbols(self, force_refresh: bool = False) -> List[str]:
        """
        Получение списка всех торговых пар
        
        Args:
            force_refresh: принудительно обновить кэш
        
        Returns:
            список символов
        """
        # Проверяем кэш (1 час)
        if not force_refresh and self._symbols_cache:
            if time.time() - self._symbols_cache_time < 3600:
                return self._symbols_cache
        
        logger.info("Загрузка списка символов...")
        
        result = self._request(self.endpoints['symbols'])
        
        symbols = []
        if result and isinstance(result, list):
            for contract in result:
                symbol = contract.get('symbol')
                if symbol and symbol.endswith('-USDT'):
                    symbols.append(symbol)
        
        # Сохраняем в кэш
        self._symbols_cache = symbols
        self._symbols_cache_time = time.time()
        
        logger.info(f"Загружено символов: {len(symbols)}")
        return symbols
    
    def load_symbols_from_file(self, file_path: str = 'bingx_symbols.json') -> List[str]:
        """
        Загрузка символов из JSON файла
        
        Args:
            file_path: путь к файлу
        
        Returns:
            список символов
        """
        symbols_path = Path(file_path)
        
        if not symbols_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            return self.get_symbols()
        
        try:
            with open(symbols_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                symbols = data.get('symbols', [])
                logger.info(f"Загружено символов из файла: {len(symbols)}")
                return symbols
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {file_path}: {e}")
            return self.get_symbols()
    
    def get_klines(self, symbol: str, interval: str = '5m', limit: int = 200) -> Optional[List[Dict]]:
        """
        Получение свечных данных
        
        Args:
            symbol: торговая пара (например, 'BTC-USDT')
            interval: таймфрейм ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
            limit: количество свечей (максимум 1440)
        
        Returns:
            список свечей в формате:
            [
                {
                    'openTime': 1234567890000,
                    'open': 50000.0,
                    'high': 50500.0,
                    'low': 49800.0,
                    'close': 50200.0,
                    'volume': 100.5,
                    ...
                },
                ...
            ]
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        result = self._request(self.endpoints['klines'], params)
        
        if not result:
            logger.warning(f"Нет данных для {symbol}")
            return None
        
        # BingX может вернуть либо список списков, либо список объектов
        candles = []
        
        # Если result - список
        if isinstance(result, list):
            for item in result:
                try:
                    # Проверяем тип элемента
                    if isinstance(item, (list, tuple)):
                        # Формат: [openTime, open, high, low, close, volume, closeTime, ...]
                        if len(item) >= 6:
                            candle = {
                                'openTime': item[0],
                                'open': float(item[1]),
                                'high': float(item[2]),
                                'low': float(item[3]),
                                'close': float(item[4]),
                                'volume': float(item[5]),
                                'closeTime': item[6] if len(item) > 6 else 0,
                                'quoteVolume': float(item[7]) if len(item) > 7 else 0,
                                'trades': item[8] if len(item) > 8 else 0,
                                'takerBuyBaseVolume': float(item[9]) if len(item) > 9 else 0,
                                'takerBuyQuoteVolume': float(item[10]) if len(item) > 10 else 0
                            }
                            candles.append(candle)
                    elif isinstance(item, dict):
                        # Формат: {'openTime': ..., 'open': ..., ...}
                        candle = {
                            'openTime': item.get('openTime', 0),
                            'open': float(item.get('open', 0)),
                            'high': float(item.get('high', 0)),
                            'low': float(item.get('low', 0)),
                            'close': float(item.get('close', 0)),
                            'volume': float(item.get('volume', 0)),
                            'closeTime': item.get('closeTime', 0),
                            'quoteVolume': float(item.get('quoteVolume', 0)),
                            'trades': item.get('trades', 0),
                            'takerBuyBaseVolume': float(item.get('takerBuyBaseVolume', 0)),
                            'takerBuyQuoteVolume': float(item.get('takerBuyQuoteVolume', 0))
                        }
                        candles.append(candle)
                except (IndexError, ValueError, TypeError) as e:
                    logger.warning(f"Ошибка парсинга свечи: {e}")
                    continue
        
        # Если result - словарь с полем 'candles'
        elif isinstance(result, dict):
            candles_data = result.get('candles') or result.get('data') or result.get('klines')
            if candles_data and isinstance(candles_data, list):
                for item in candles_data:
                    try:
                        if isinstance(item, dict):
                            candle = {
                                'openTime': item.get('openTime', 0),
                                'open': float(item.get('open', 0)),
                                'high': float(item.get('high', 0)),
                                'low': float(item.get('low', 0)),
                                'close': float(item.get('close', 0)),
                                'volume': float(item.get('volume', 0)),
                                'closeTime': item.get('closeTime', 0),
                                'quoteVolume': float(item.get('quoteVolume', 0)),
                                'trades': item.get('trades', 0),
                                'takerBuyBaseVolume': float(item.get('takerBuyBaseVolume', 0)),
                                'takerBuyQuoteVolume': float(item.get('takerBuyQuoteVolume', 0))
                            }
                            candles.append(candle)
                    except Exception as e:
                        logger.warning(f"Ошибка парсинга свечи: {e}")
                        continue
        
        if not candles:
            logger.warning(f"Не удалось распарсить свечи для {symbol}")
            return None
        
        return candles
    
    def get_all_klines(self, symbols: List[str], interval: str = '5m', limit: int = 200, 
                      max_workers: int = 10) -> Dict[str, List[Dict]]:
        """
        Получение свечных данных для всех символов
        
        Args:
            symbols: список символов
            interval: таймфрейм
            limit: количество свечей
            max_workers: количество потоков
        
        Returns:
            словарь {symbol: candles}
        """
        import concurrent.futures
        
        result = {}
        total = len(symbols)
        
        def fetch_one(symbol):
            return symbol, self.get_klines(symbol, interval, limit)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_one, s): s for s in symbols}
            
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                symbol = futures[future]
                try:
                    sym, candles = future.result(timeout=30)
                    if candles:
                        result[sym] = candles
                    if i % 50 == 0:
                        logger.info(f"Прогресс: {i}/{total} | Загружено: {len(result)}")
                except Exception as e:
                    logger.error(f"Ошибка загрузки {symbol}: {e}")
        
        logger.info(f"Загружено: {len(result)}/{total}")
        return result


# Функция для быстрого получения свечей (совместимость со старым кодом)
def get_klines(symbol: str, interval: str = '5m', limit: int = 200) -> Optional[List[Dict]]:
    """
    Быстрая функция получения свечей
    
    Args:
        symbol: торговая пара
        interval: таймфрейм
        limit: количество свечей
    
    Returns:
        список свечей
    """
    client = BingXKlineData(testnet=True)
    return client.get_klines(symbol, interval, limit)


def get_all_symbols_from_api() -> List[str]:
    """
    Получение всех символов из API
    """
    client = BingXKlineData(testnet=True)
    return client.get_symbols()


def load_symbols_from_file(file_path: str = 'bingx_symbols.json') -> List[str]:
    """
    Загрузка символов из файла
    """
    client = BingXKlineData(testnet=True)
    return client.load_symbols_from_file(file_path)


# Пример использования
if __name__ == "__main__":
    print("="*60)
    print("ТЕСТИРОВАНИЕ KLINE DATA")
    print("="*60)
    
    # Создаем клиент
    client = BingXKlineData(testnet=True)
    
    # Получаем свечи для BTC
    print("\n1. Тест получения свечей BTC-USDT:")
    candles = client.get_klines("BTC-USDT", interval="5m", limit=10)
    
    if candles:
        print(f"   Получено свечей: {len(candles)}")
        latest = candles[-1]
        print(f"   Последняя свеча:")
        print(f"      Время: {datetime.fromtimestamp(latest['openTime']/1000)}")
        print(f"      Open: {latest['open']:.2f}")
        print(f"      High: {latest['high']:.2f}")
        print(f"      Low: {latest['low']:.2f}")
        print(f"      Close: {latest['close']:.2f}")
        print(f"      Volume: {latest['volume']:.2f}")
    else:
        print("   ❌ Не удалось получить свечи")
    
    # Загружаем символы из файла
    print("\n2. Загрузка символов из файла:")
    symbols = load_symbols_from_file('bingx_symbols.json')
    print(f"   Загружено символов: {len(symbols)}")
    if symbols:
        print(f"   Первые 5: {symbols[:5]}")
    
    # Тест быстрой функции
    print("\n3. Тест быстрой функции get_klines:")
    candles = get_klines("ETH-USDT", interval="5m", limit=5)
    if candles:
        print(f"   Получено свечей ETH: {len(candles)}")
    else:
        print("   ❌ Не удалось получить свечи")
    
    print("\n" + "="*60)
    print("Тест завершен")
    print("="*60)