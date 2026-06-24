# bx_position_editor.py
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger('PositionEditor')

@dataclass
class PositionToFix:
    """Позиция, требующая исправления защиты"""
    symbol: str
    side: str
    position_side: str
    quantity: float
    stop_percent: float
    take_percent: float
    entry_price: float
    order_id: int
    attempts: int = 0
    last_attempt: float = 0
    next_attempt_delay: float = 2

class PositionEditor:
    """
    Сервис для проверки и исправления стоп/тейк ордеров
    Использует ТОЛЬКО эталонные проценты из positionSizing
    """
    
    def __init__(self, trader, max_attempts=10, base_delay=2, max_delay=60):
        self.trader = trader
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.positions_to_fix = []  # Позиции, требующие исправления
        self.rate_limit_until = 0
        
    def _get_price_precision(self, price: float) -> int:
        """Определяет нужное количество знаков после запятой для цены"""
        if price < 0.0001:
            return 8
        elif price < 0.001:
            return 7
        elif price < 0.01:
            return 6
        elif price < 0.1:
            return 5
        elif price < 1:
            return 4
        elif price < 10:
            return 3
        else:
            return 2
    
    def _get_min_price_step(self, price: float) -> float:
        """Возвращает минимальный шаг цены для данного диапазона"""
        if price < 0.0001:
            return 0.000001
        elif price < 0.001:
            return 0.00001
        elif price < 0.01:
            return 0.0001
        elif price < 0.1:
            return 0.001
        elif price < 1:
            return 0.01
        elif price < 10:
            return 0.1
        else:
            return 1.0
    
    def _ensure_min_distance(self, price: float, target: float, min_step: float) -> float:
        """Гарантирует минимальное расстояние между ценой и целевым уровнем"""
        if abs(target - price) < min_step * 2:
            if target > price:
                return price + min_step * 2
            else:
                return price - min_step * 2
        return target
    
    def scan_open_positions(self):
        """
        Сканирует все открытые позиции и проверяет их защиту
        Добавляет в очередь те, у которых защита неполная
        """
        print(f"\n🔍 СКАНИРОВАНИЕ ОТКРЫТЫХ ПОЗИЦИЙ")
        
        try:
            # Получаем все открытые позиции с биржи
            positions = self.trader.get_positions()
            if not positions:
                print("   Нет открытых позиций")
                return
            
            # Получаем все открытые ордера (стопы и тейки)
            open_orders = self.trader.get_open_orders()
            
            # Для каждой позиции проверяем наличие защиты
            for pos in positions:
                symbol = pos.get('symbol')
                position_side = pos.get('positionSide')
                quantity = float(pos.get('positionAmt', 0))
                entry_price = float(pos.get('entryPrice', 0))
                
                # Определяем сторону для закрытия
                side = 'BUY' if position_side == 'LONG' else 'SELL'
                
                # Ищем стоп и тейк ордера для этой позиции
                has_stop = False
                has_take = False
                
                for order in open_orders:
                    if order.get('symbol') != symbol:
                        continue
                    if order.get('positionSide') != position_side:
                        continue
                    
                    order_type = order.get('type')
                    if order_type == 'STOP_MARKET':
                        has_stop = True
                    elif order_type == 'TAKE_PROFIT_MARKET':
                        has_take = True
                
                # Логируем состояние
                status = "🟢 ПОЛНАЯ" if (has_stop and has_take) else \
                        "🟡 ЧАСТИЧНАЯ" if (has_stop or has_take) else \
                        "🔴 БЕЗ ЗАЩИТЫ"
                
                print(f"   {status} {symbol}: стоп={has_stop}, тейк={has_take}")
                
                # Если защита неполная - добавляем в очередь на исправление
                if not (has_stop and has_take):
                    # Здесь должны быть реальные проценты из БД или сигнала
                    # Пока используем эталонные значения по умолчанию
                    stop_percent = 0.2  # 0.2 ATR
                    take_percent = 0.5  # 0.5 ATR
                    
                    # Проверяем, нет ли уже этой позиции в очереди
                    existing = [p for p in self.positions_to_fix if p.symbol == symbol]
                    if not existing:
                        self.positions_to_fix.append(PositionToFix(
                            symbol=symbol,
                            side=side,
                            position_side=position_side,
                            quantity=quantity,
                            stop_percent=stop_percent,
                            take_percent=take_percent,
                            entry_price=entry_price,
                            order_id=0  # ID не важен для существующих позиций
                        ))
                        print(f"      ➡️ Добавлена в очередь на исправление (стоп {stop_percent}%, тейк {take_percent}%)")
                
        except Exception as e:
            print(f"   ❌ Ошибка сканирования: {e}")
    
    def process_fixes(self) -> Dict[str, int]:
        """
        Обрабатывает очередь позиций, требующих исправления
        Использует ТОЛЬКО эталонные проценты для расчета уровней
        """
        if not self.positions_to_fix:
            return {'fixed': 0, 'total': 0, 'failed': 0, 'pending': 0}
        
        print(f"\n🔧 ИСПРАВЛЕНИЕ {len(self.positions_to_fix)} ПОЗИЦИЙ")
        
        fixed = 0
        failed = 0
        still_pending = []
        
        for pos in self.positions_to_fix:
            if pos.attempts >= self.max_attempts:
                print(f"   ⚠️ {pos.symbol}: превышено попыток ({pos.attempts}) - ПРИНУДИТЕЛЬНОЕ ЗАКРЫТИЕ")
                self._close_position(pos)
                failed += 1
                continue
            
            print(f"\n   🔄 {pos.symbol} (попытка {pos.attempts + 1}/{self.max_attempts})")
            
            # Получаем текущие ордера для этой позиции
            try:
                open_orders = self.trader.get_open_orders(pos.symbol)
                
                has_stop = False
                has_take = False
                
                for order in open_orders:
                    if order.get('positionSide') != pos.position_side:
                        continue
                    order_type = order.get('type')
                    if order_type == 'STOP_MARKET':
                        has_stop = True
                    elif order_type == 'TAKE_PROFIT_MARKET':
                        has_take = True
                
                print(f"      Текущее состояние: стоп={has_stop}, тейк={has_take}")
                
                # Если защита уже полная - убираем из очереди
                if has_stop and has_take:
                    print(f"      ✅ Защита уже полная")
                    fixed += 1
                    continue
                
                # Получаем текущую цену для расчета
                current_price = self.trader._get_current_price(pos.symbol)
                if not current_price:
                    print(f"      ⚠️ Нет цены, повтор")
                    pos.attempts += 1
                    still_pending.append(pos)
                    continue
                
                # Рассчитываем целевые уровни по ЭТАЛОННЫМ процентам
                precision = self._get_price_precision(current_price)
                min_step = self._get_min_price_step(current_price)
                
                if pos.side == "BUY":  # LONG
                    target_stop = current_price * (1 - pos.stop_percent / 100)
                    target_take = current_price * (1 + pos.take_percent / 100)
                    # Проверяем корректность
                    if target_stop >= current_price:
                        print(f"      ⚠️ Стоп должен быть ниже цены, корректируем")
                        target_stop = current_price * (1 - pos.stop_percent * 2 / 100)
                else:  # SHORT
                    target_stop = current_price * (1 + pos.stop_percent / 100)
                    target_take = current_price * (1 - pos.take_percent / 100)
                    # Проверяем корректность
                    if target_stop <= current_price:
                        print(f"      ⚠️ Стоп должен быть выше цены, корректируем")
                        target_stop = current_price * (1 + pos.stop_percent * 2 / 100)
                
                # Округляем и проверяем минимальное расстояние
                target_stop = round(target_stop, precision)
                target_take = round(target_take, precision)
                
                target_stop = self._ensure_min_distance(current_price, target_stop, min_step)
                target_take = self._ensure_min_distance(current_price, target_take, min_step)
                
                # Убеждаемся, что стоп и тейк не совпали
                if target_stop == target_take:
                    print(f"      ⚠️ Стоп и тейк совпали, раздвигаем")
                    if pos.side == "BUY":
                        target_stop = current_price * (1 - pos.stop_percent * 1.5 / 100)
                        target_take = current_price * (1 + pos.take_percent * 1.5 / 100)
                    else:
                        target_stop = current_price * (1 + pos.stop_percent * 1.5 / 100)
                        target_take = current_price * (1 - pos.take_percent * 1.5 / 100)
                    target_stop = round(target_stop, precision)
                    target_take = round(target_take, precision)
                
                print(f"      📊 Текущая цена: {current_price:.{precision}f}")
                print(f"      🛑 Целевой стоп: {target_stop:.{precision}f} ({pos.stop_percent}%)")
                print(f"      🎯 Целевой тейк: {target_take:.{precision}f} ({pos.take_percent}%)")
                
                close_side = 'SELL' if pos.side == 'BUY' else 'BUY'
                fix_success = True
                
                # Если нет стопа - добавляем
                if not has_stop:
                    print(f"      🛑 Добавление стопа...")
                    stop_params = {
                        'symbol': pos.symbol,
                        'side': close_side,
                        'positionSide': pos.position_side,
                        'type': 'STOP_MARKET',
                        'quantity': '100',
                        'stopPrice': str(target_stop),
                        'workingType': 'MARK_PRICE'
                    }
                    try:
                        self.trader._request('POST', self.trader.endpoints['order'], stop_params)
                        print(f"      ✅ Стоп добавлен")
                    except Exception as e:
                        print(f"      ❌ Ошибка добавления стопа: {e}")
                        fix_success = False
                
                time.sleep(0.5)
                
                # Если нет тейка - добавляем
                if not has_take:
                    print(f"      🎯 Добавление тейка...")
                    take_params = {
                        'symbol': pos.symbol,
                        'side': close_side,
                        'positionSide': pos.position_side,
                        'type': 'TAKE_PROFIT_MARKET',
                        'quantity': '100',
                        'stopPrice': str(target_take),
                        'workingType': 'MARK_PRICE'
                    }
                    try:
                        self.trader._request('POST', self.trader.endpoints['order'], take_params)
                        print(f"      ✅ Тейк добавлен")
                    except Exception as e:
                        print(f"      ❌ Ошибка добавления тейка: {e}")
                        fix_success = False
                
                if fix_success:
                    print(f"      ✅ Защита исправлена")
                    fixed += 1
                else:
                    pos.attempts += 1
                    still_pending.append(pos)
                    print(f"      ⏳ Будет повтор ({pos.attempts}/{self.max_attempts})")
                    
            except Exception as e:
                print(f"      ❌ Ошибка обработки: {e}")
                pos.attempts += 1
                still_pending.append(pos)
        
        self.positions_to_fix = still_pending
        return {'fixed': fixed, 'total': fixed + failed + len(still_pending), 
                'failed': failed, 'pending': len(still_pending)}
    
    def _close_position(self, pos: PositionToFix):
        """Принудительное закрытие позиции"""
        print(f"      🚨 ПРИНУДИТЕЛЬНОЕ ЗАКРЫТИЕ {pos.symbol}")
        try:
            close_side = 'SELL' if pos.side == 'BUY' else 'BUY'
            close_params = {
                'symbol': pos.symbol,
                'side': close_side,
                'positionSide': pos.position_side,
                'type': 'MARKET',
                'quantity': '100'
            }
            self.trader._request('POST', self.trader.endpoints['order'], close_params)
            print(f"      ✅ Позиция закрыта")
        except Exception as e:
            print(f"      ❌ Ошибка закрытия: {e}")
    
    def run_fixer(self, interval=10):
        """Запускает цикл проверки и исправления"""
        print(f"\n🚀 РЕДАКТОР ЗАПУЩЕН (интервал {interval}с)")
        try:
            while True:
                # Сканируем открытые позиции
                self.scan_open_positions()
                
                # Исправляем найденные проблемы
                if self.positions_to_fix:
                    stats = self.process_fixes()
                    print(f"\n📊 Статистика: ✅{stats['fixed']} / ⌛{stats['pending']} / ❌{stats['failed']}")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n🛑 Редактор остановлен")