# bx_api.py
import time
import hmac
import hashlib
import requests
import urllib.parse
import logging
from typing import Optional, Dict, List, Any
from config_loader import config

logger = logging.getLogger('BxAPI')

class BingXAPI:
    """
    Чистый API клиент для BingX
    Только отправка запросов, никакой логики
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: Optional[bool] = None):
        self.api_key = api_key or config.api_key
        self.api_secret = api_secret or config.api_secret
        self.testnet = testnet if testnet is not None else config.testnet
        
        # Определяем базовую валюту и URL
        self.base_currency = 'VST' if self.testnet else 'USDT'
        self.base_url = "https://open-api-vst.bingx.com" if self.testnet else "https://open-api.bingx.com"
        
        # Эндпоинты
        self.endpoints = {
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
        
        self.session = requests.Session()
        self.session.headers.update({'X-BX-APIKEY': self.api_key})
        
        # Кэш для минимальных количеств
        self.min_quantities = {}
        self._load_min_quantities()
        
        logger.info(f"API клиент инициализирован ({'тестнет' if self.testnet else 'реальная'})")
    
    def _load_min_quantities(self):
        """Загружает минимальные количества для всех монет"""
        try:
            response = requests.get(f"{self.base_url}{self.endpoints['contracts']}")
            data = response.json()
            
            if data.get('code') == 0:
                for contract in data.get('data', []):
                    symbol = contract.get('symbol')
                    min_qty = float(contract.get('minQuantity', 0))
                    if symbol and min_qty > 0:
                        self.min_quantities[symbol] = min_qty
        except Exception as e:
            logger.warning(f"Не удалось загрузить минимальные количества: {e}")
    
    def _get_server_time(self) -> int:
        """Получение серверного времени"""
        response = self.session.get(f"{self.base_url}{self.endpoints['server_time']}", timeout=5)
        data = response.json()
        if data.get('code') == 0:
            return data['data']['serverTime']
        raise Exception(f"Ошибка получения времени: {data}")
    
    def _generate_signature(self, params_str: str) -> str:
        """Генерация подписи"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            params_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def request(self, method: str, path: str, params: Dict = None) -> Any:
        """Универсальный метод запроса с подписью"""
        if params is None:
            params = {}
        
        # Добавляем timestamp
        timestamp = self._get_server_time()
        request_params = params.copy()
        request_params['timestamp'] = timestamp
        request_params['recvWindow'] = '5000'
        
        # Сортируем и формируем строку для подписи
        sorted_keys = sorted(request_params.keys())
        params_list = [f"{k}={request_params[k]}" for k in sorted_keys]
        params_str = '&'.join(params_list)
        
        # Подпись
        signature = self._generate_signature(params_str)
        
        # Формируем URL с параметрами
        url_params_list = []
        for key in sorted_keys:
            value = str(request_params[key])
            if any(c in value for c in '{[}"]'):
                value = urllib.parse.quote(value, safe='')
            url_params_list.append(f"{key}={value}")
        
        url = f"{self.base_url}{path}?{'&'.join(url_params_list)}&signature={signature}"
        
        # Отправляем запрос
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=10)    
            else:
                response = self.session.post(url, timeout=10)
            
            result = response.json()
            
            if result.get('code') != 0:
                raise Exception(f"API Error: {result.get('msg')}")
            
            return result.get('data', {})
            
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    def get_min_qty(self, symbol: str) -> float:
        """Возвращает минимальное количество для символа"""
        return self.min_quantities.get(symbol, 0.001)