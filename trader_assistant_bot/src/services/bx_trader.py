# bx_trader.py
import time
import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from bx_api import BingXAPI
from bx_risk_manager import RiskManager

logger = logging.getLogger('BxTraderAdvanced')

class BingXTrader:
    """
    Расширенная логика торговли с поддержкой стопов и тейков на бирже
    и принудительной проверкой плеча
    """
    
    def __init__(self, api: Optional[BingXAPI] = None, required_leverage: int = 1, risk_manager: Optional[RiskManager] = None):
        self.api = api or BingXAPI()
        self.base_currency = self.api.base_currency
        self.required_leverage = required_leverage
        self.db_writer = None
        self.risk_manager = risk_manager
        
        # Кэш для баланса
        self._balance_cache = None
        self._balance_time = 0
        
        # Кэш для проверки плеча
        self._leverage_checked = {}  # {symbol: timestamp}
        self._leverage_check_interval = 3600  # Проверять раз в час
        
        logger.info(f"Trader Advanced инициализирован (плечо: {required_leverage}x)")
    
    def _check_leverage(self, symbol: str, force: bool = False) -> Tuple[bool, str]:
        """
        Проверяет и принудительно устанавливает плечо 1x
        Возвращает (успешно, сообщение)
        """
        now = time.time()
        
        # Проверяем, нужно ли обновлять
        if not force and symbol in self._leverage_checked:
            if now - self._leverage_checked[symbol] < self._leverage_check_interval:
                return True, f"Плечо уже проверено для {symbol}"
        
        try:
            # Получаем текущее плечо
            params = {'symbol': symbol}
            result = self.api.request('GET', self.api.endpoints['leverage'], params)
            
            current_leverage = None
            if isinstance(result, dict):
                # Пытаемся найти плечо в ответе
                if 'longLeverage' in result:
                    current_leverage = float(result.get('longLeverage', 0))
                elif 'leverage' in result:
                    current_leverage = float(result.get('leverage', 0))
            
            # Если плечо не соответствует требуемому - устанавливаем
            if current_leverage != self.required_leverage:
                logger.warning(f"⚠️ {symbol}: текущее плечо {current_leverage}x, устанавливаем {self.required_leverage}x")
                
                # Устанавливаем для LONG и SHORT
                params_long = {'symbol': symbol, 'leverage': self.required_leverage, 'side': 'LONG'}
                params_short = {'symbol': symbol, 'leverage': self.required_leverage, 'side': 'SHORT'}
                
                self.api.request('POST', self.api.endpoints['leverage'], params_long)
                self.api.request('POST', self.api.endpoints['leverage'], params_short)
                
                logger.info(f"✅ Плечо {self.required_leverage}x установлено для {symbol}")
            
            # Запоминаем время проверки
            self._leverage_checked[symbol] = now
            return True, f"Плечо {self.required_leverage}x OK"
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки плеча для {symbol}: {e}")
            return False, f"Ошибка проверки плеча: {e}"
    
    def get_balance(self, force_refresh: bool = False) -> float:
        """Получает доступный баланс (equity)"""
        if not force_refresh and self._balance_cache and time.time() - self._balance_time < 5:
            return self._balance_cache
        
        try:
            result = self.api.request('GET', self.api.endpoints['balance'])
            
            balance = 0.0
            
            if isinstance(result, list) and len(result) > 0:
                for item in result:
                    asset = item.get('asset', '').upper()
                    if asset in ['USDT', 'VST', self.base_currency]:
                        balance = float(item.get('equity', item.get('balance', 0)))
                        break
                else:
                    balance = float(result[0].get('equity', result[0].get('balance', 0)))
            
            elif isinstance(result, dict):
                if 'balance' in result and isinstance(result['balance'], dict):
                    balance = float(result['balance'].get('equity', result['balance'].get('balance', 0)))
                else:
                    balance = float(result.get('equity', result.get('balance', 0)))
            
            self._balance_cache = balance
            self._balance_time = time.time()
            return balance
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return 0.0
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Получает открытые позиции"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        try:
            result = self.api.request('GET', self.api.endpoints['positions'], params)
            
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'positions' in result:
                return result['positions']
            return []
        except Exception as e:
            logger.error(f"Ошибка получения позиций: {e}")
            return []
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Получает текущую цену символа"""
        try:
            params = {'symbol': symbol}
            result = self.api.request('GET', self.api.endpoints['ticker'], params)
            
            if isinstance(result, list) and len(result) > 0:
                return float(result[0].get('lastPrice', 0))
            elif isinstance(result, dict):
                return float(result.get('lastPrice', 0))
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
            return None
    
    def open_position_with_stops(self, 
                                symbol: str, 
                                side: str, 
                                quantity: float,
                                stop_loss_price: float,
                                take_profit_price: float,
                                force_leverage_check: bool = True,
                                market_data: Dict = None) -> Optional[Dict]:
        try:

            # === 0. ПРОВЕРКА BLACKLIST ЧЕРЕЗ RISK_MANAGER ===
            if self.risk_manager:
                can_trade, reason = self.risk_manager.can_trade_symbol(symbol, market_data)
                if not can_trade:
                    logger.error(f"❌ {symbol}: {reason}")
                    return None

            # === 1. ПРОВЕРКА ПЛЕЧА ===
            if force_leverage_check:
                ok, msg = self._check_leverage(symbol)
                if not ok:
                    logger.error(f"❌ {symbol}: {msg}")
                    return None
                logger.debug(f"✅ {symbol}: {msg}")
            
            # === 2. ПРОВЕРКА МИНИМАЛЬНОГО КОЛИЧЕСТВА ===
            min_qty = self.api.get_min_qty(symbol)
            if quantity < min_qty:
                logger.warning(f"⚠️ {symbol}: количество {quantity} < {min_qty}, увеличиваем")
                quantity = min_qty
            
            # === 3. ПОЛУЧАЕМ ТЕКУЩУЮ ЦЕНУ ===
            current_price = self.get_current_price(symbol) or 0
            if current_price == 0:
                logger.error(f"❌ {symbol}: не удалось получить текущую цену")
                return None
            
            # === 4. ОПРЕДЕЛЯЕМ СТОРОНЫ ===
            position_side = 'LONG' if side == 'BUY' else 'SHORT'
            
             # === 5. ОТКРЫВАЕМ ПОЗИЦИЮ ===
            params = {
                'symbol': symbol,
                'side': side,
                'positionSide': position_side,
                'type': 'MARKET',
                'quantity': str(quantity),
                'newClientOrderId': f"open_{int(time.time())}"
            }
            
            logger.info(f"📤 Открытие {symbol}: {side} {quantity}")
            result = self.api.request('POST', self.api.endpoints['order'], params)
            
            order_id = result.get('orderId') or result.get('order_id') or 0
            if order_id == 0:
                order_id = int(time.time() * 1000) % 1000000
            
            # Небольшая пауза для гарантии, что позиция открыта
            time.sleep(0.5)
            
            logger.info(f"✅ Позиция открыта: {symbol} {side} {quantity} | "
                       f"Стоп: {stop_loss_price:.6f} | Тейк: {take_profit_price:.6f}")
            
            # === 6. УСТАНАВЛИВАЕМ СТОП-ЛОСС ===
            # Сторона для закрытия (противоположная открытию)
            stop_side = 'SELL' if side == 'BUY' else 'BUY'
            stop_quantity = quantity * 0.99
            stop_params = {
                'symbol': symbol,
                'side': stop_side,
                'positionSide': position_side,  # ← ТА ЖЕ, ЧТО У ПОЗИЦИИ!
                'type': 'STOP_MARKET',
                'quantity': str(stop_quantity),
                'stopPrice': str(stop_loss_price),
                'workingType': 'MARK_PRICE',
                'newClientOrderId': f"stop_{int(time.time())}"
            }
            
            logger.info(f"🛑 Установка стопа {symbol}: {stop_loss_price:.6f}")
            stop_result = self.api.request('POST', self.api.endpoints['order'], stop_params)
            stop_order_id = stop_result.get('orderId') or stop_result.get('order_id') or 0
            
            # === 7. УСТАНАВЛИВАЕМ ТЕЙК-ПРОФИТ ===
            take_params = {
                'symbol': symbol,
                'side': stop_side,
                'positionSide': position_side,  
                'type': 'TAKE_PROFIT_MARKET',
                'quantity': str(stop_quantity),
                'stopPrice': str(take_profit_price),
                'workingType': 'MARK_PRICE',
                'newClientOrderId': f"take_{int(time.time())}"
            }
            
            logger.info(f"🎯 Установка тейка {symbol}: {take_profit_price:.6f}")
            take_result = self.api.request('POST', self.api.endpoints['order'], take_params)
            take_order_id = take_result.get('orderId') or take_result.get('order_id') or 0

            if hasattr(self, 'db_writer') and self.db_writer:
                try:
                    # Проценты стопа и тейка нужно передавать извне!
                    # Сейчас в методе нет stop_percent/take_percent
                    # ВРЕМЕННО: используй 0.2 и 0.5 или добавь параметры в метод
                    self.db_writer.add_position(
                        symbol=symbol,
                        side=side,
                        entry_price=current_price,
                        quantity=quantity,
                        stop_percent=0.2,  # ← ВРЕМЕННО! Нужно передавать
                        take_percent=0.5,  # ← ВРЕМЕННО! Нужно передавать
                        metadata={
                            'order_id': order_id,
                            'stop_order_id': stop_order_id,
                            'take_order_id': take_order_id,
                            'stop_loss': stop_loss_price,
                            'take_profit': take_profit_price
                        }
                    )
                    logger.info(f"💾 Позиция записана в БД: {symbol}")
                except Exception as e:
                    logger.error(f"❌ Ошибка записи в БД: {e}")
            
            return {
                'order_id': order_id,
                'stop_order_id': stop_order_id,
                'take_order_id': take_order_id,
                'symbol': symbol,
                'side': side,
                'position_side': position_side,
                'quantity': quantity,
                'entry_price': current_price,
                'stop_loss': stop_loss_price,
                'take_profit': take_profit_price,
                'status': 'OPEN'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка открытия позиции {symbol}: {e}")
            return None
    
    def close_position(self, symbol: str) -> bool:
        """Закрывает позицию и удаляет стопы/тейки"""
        try:
            # Получаем текущую позицию
            positions = self.get_positions(symbol)
            if not positions:
                logger.warning(f"Позиция {symbol} не найдена")
                return False
            
            pos = positions[0]
            position_side = pos.get('positionSide')
            close_side = 'SELL' if position_side == 'LONG' else 'BUY'
            qty = abs(float(pos.get('positionAmt', 0)))
            
            # Отменяем все лимитные/стоп ордера по этому символу
            try:
                self.cancel_all_orders(symbol)
            except:
                pass
            
            # Закрываем позицию
            params = {
                'symbol': symbol,
                'side': close_side,
                'positionSide': position_side,
                'type': 'MARKET',
                'quantity': str(qty)
            }
            
            self.api.request('POST', self.api.endpoints['order'], params)
            logger.info(f"✅ Позиция {symbol} закрыта")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка закрытия позиции {symbol}: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Отменяет все ордера по символу"""
        try:
            params = {'symbol': symbol}
            self.api.request('DELETE', self.api.endpoints['cancelAllOrders'], params)
            logger.debug(f"Ордера отменены для {symbol}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отмены ордеров {symbol}: {e}")
            return False
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Получает открытые ордера"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        try:
            result = self.api.request('GET', self.api.endpoints['openOrders'], params)
            if isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error(f"Ошибка получения ордеров: {e}")
            return []
    
    def update_stops(self, symbol: str, new_stop_loss: float = None, new_take_profit: float = None) -> bool:
        """Обновляет стоп-лосс и тейк-профит"""

        
        try:
            # Получаем позицию
            positions = self.get_positions(symbol)
            if not positions:
                logger.warning(f"Позиция {symbol} не найдена")
                return False
            
            pos = positions[0]
            position_side = pos.get('positionSide')
            qty = abs(float(pos.get('positionAmt', 0)))
            
            # Отменяем старые стоп-ордера
            self.cancel_all_orders(symbol)
            
            # Определяем стороны для стопов
            stop_side = 'SELL' if position_side == 'LONG' else 'BUY'
            stop_position_side = 'LONG' if stop_side == 'SELL' else 'SHORT'
            
            # Устанавливаем новый стоп
            if new_stop_loss:
                stop_params = {
                    'symbol': symbol,
                    'side': stop_side,
                    'positionSide': stop_position_side,
                    'type': 'STOP_MARKET',
                    'quantity': str(qty),
                    'stopPrice': str(new_stop_loss),
                    'workingType': 'MARK_PRICE'
                }
                self.api.request('POST', self.api.endpoints['order'], stop_params)
                logger.info(f"🔄 Стоп обновлен {symbol}: {new_stop_loss:.6f}")
            
            # Устанавливаем новый тейк
            if new_take_profit:
                take_params = {
                    'symbol': symbol,
                    'side': stop_side,
                    'positionSide': stop_position_side,
                    'type': 'TAKE_PROFIT_MARKET',
                    'quantity': str(qty),
                    'stopPrice': str(new_take_profit),
                    'workingType': 'MARK_PRICE'
                }
                self.api.request('POST', self.api.endpoints['order'], take_params)
                logger.info(f"🔄 Тейк обновлен {symbol}: {new_take_profit:.6f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления стопов {symbol}: {e}")
            return False

    
    def force_check_all_leverages(self, symbols: List[str]) -> Dict[str, bool]:
        """Принудительно проверяет плечо для списка символов"""
        results = {}
        for symbol in symbols:
            ok, msg = self._check_leverage(symbol, force=True)
            results[symbol] = ok
            if ok:
                logger.info(f"✅ {symbol}: {msg}")
            else:
                logger.error(f"❌ {symbol}: {msg}")
            time.sleep(0.5)  # Избегаем rate limit
        return results


# Пример использования:
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    api = BingXAPI()
    trader = BingXTrader(api, required_leverage=1)
    
    # Пример открытия позиции со стопами
    result = trader.open_position_with_stops(
        symbol="BTC-USDT",
        side="BUY",
        quantity=0.001,
        stop_loss_price=49000.0,
        take_profit_price=51000.0
    )
    
    if result:
        print(f"Позиция открыта: {result}")