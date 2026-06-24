# bx_monitor.py
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from collections import deque
import threading
from positionSizing import positionSizing

logger = logging.getLogger('BxMonitor')

@dataclass
class Position:
    """Торговая позиция"""
    symbol: str
    side: str  # 'BUY' для LONG, 'SELL' для SHORT
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_percent: float      
    take_percent: float      
    status: str = "OPEN"


class BxMonitor:
    """
    Модуль для мониторинга позиций
    Принимает решения на основе percentage с биржи
    """
    
    def __init__(self, trader, orchestrator=None):
        self.trader = trader
        self.orchestrator = orchestrator
        self.positions = {}  # {symbol: Position}
        self.last_positions_data = {}
        
        # Rate limiting
        self._api_call_timestamps = deque(maxlen=100)
        self._max_calls_per_second = 5
    
    def _check_rate_limit(self):
        """Проверка лимита запросов"""
        now = time.time()
        while self._api_call_timestamps and self._api_call_timestamps[0] < now - 1:
            self._api_call_timestamps.popleft()
        
        if len(self._api_call_timestamps) >= self._max_calls_per_second:
            sleep_time = 1 - (now - self._api_call_timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self._api_call_timestamps.append(now)
    
    def add_position(self, symbol: str, side: str, entry_price: float, 
                    quantity: float, stop_percent: float, take_percent: float) -> Position:
        """Добавляет позицию для мониторинга"""
        pos = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_percent=stop_percent,
            take_percent=take_percent
        )
        
        self.positions[symbol] = pos
        print(f"   📊 Добавлена позиция {symbol}: стоп {stop_percent}%, тейк {take_percent}%")
        return pos
    
    def sync_positions(self):
        """Синхронизация с биржей"""
        print(f"\n🔄 СИНХРОНИЗАЦИЯ [{datetime.now().strftime('%H:%M:%S')}]")
        self._check_rate_limit()
        
        try:
            # Получаем все позиции с биржи
            all_positions = self.trader.get_positions()
            
            if not all_positions:
                return
            
            self.last_positions_data = {}
            exchange_symbols = set()
            positions_data = {}
            
            # Множество позиций на бирже
            exchange_symbols = set()
            positions_data = {}
            
            for pos_data in all_positions:
                symbol = pos_data.get('symbol')
                position_amt = float(pos_data.get('positionAmt', 0))
                
                if position_amt != 0:
                    exchange_symbols.add(symbol)
                    positions_data[symbol] = pos_data
                    self.last_positions_data[symbol] = pos_data
            
                # ДОБАВЛЯЕМ НОВЫЕ ПОЗИЦИИ
            for symbol, pos_data in positions_data.items():
                if symbol not in self.positions:
                    print(f"   ➕ Новая позиция на бирже: {symbol}")
                    
                    # Определяем сторону
                    position_side = pos_data.get('positionSide', 'LONG')
                    side = 'BUY' if position_side == 'LONG' else 'SELL'
                    
                    # Получаем цену входа
                    entry_price = float(pos_data.get('avgPrice', pos_data.get('entryPrice', 0)))
                    if entry_price == 0:
                        entry_price = float(pos_data.get('markPrice', 0))
                    
                    quantity = abs(float(pos_data.get('positionAmt', 0)))
                
                    atr = 0
                    if 'atr' in pos_data:
                        atr = float(pos_data.get('atr', 0))
                    else:
                        # Запасной вариант: ATR = 0.5% от цены
                        atr = entry_price * 0.005
                    
                    # Вызываем positionSizing для расчета процентов
                    sizing = positionSizing(
                        capital=self.trader.get_balance(),
                        price=entry_price,
                        atr=atr,
                        direction='UP' if side == 'BUY' else 'DOWN',
                        stop_loss_mult=1.5,
                        take_profit_mult=3.25,
                        target_position_usdt=5.5
                    )
                    
                    stop_percent = sizing['stop_percent']
                    take_percent = sizing['take_percent']
                    
                    print(f"   📊 Рассчитано: стоп {stop_percent:.2f}%, тейк {take_percent:.2f}% (ATR: {sizing['atr_pct']:.2f}%)") 
                
                    # Добавляем позицию в мониторинг
                    self.add_position(
                        symbol=symbol,
                        side=side,
                        entry_price=entry_price,
                        quantity=quantity,
                        stop_percent=stop_percent,
                        take_percent=take_percent
                    )

            # Проверяем каждую позицию из нашего кэша
            for symbol in list(self.positions.keys()):
                if symbol not in exchange_symbols:
                    print(f"   ❌ {symbol}: позиция закрыта на бирже")
                    del self.positions[symbol]
                    continue
                
                # Получаем данные с биржи
                pos_data = positions_data[symbol]
                current_price = float(pos_data.get('markPrice', 0))
                
                pnl_percent = 0.0
                if 'pnlRatio' in pos_data:
                    pnl_percent = float(pos_data['pnlRatio']) * 100
                elif 'unrealizedProfit' in pos_data and 'positionValue' in pos_data:
                    unrealized = float(pos_data.get('unrealizedProfit', 0))
                    position_value = float(pos_data.get('positionValue', 0))
                    if position_value > 0:
                        pnl_percent = (unrealized / position_value) * 100
                
                # Получаем нашу позицию
                my_pos = self.positions[symbol]
                
                # ВЫВОДИМ ИНФОРМАЦИЮ
                arrow = "🟢" if my_pos.side == "BUY" else "🔴"
                print(f"   {arrow} {symbol:<12} | "
                      f"Цена: {current_price:.6f} | "
                      f"PnL: {pnl_percent:+.2f}% | "
                      f"Стоп: {my_pos.stop_percent:.2f}% | "
                      f"Тейк: {my_pos.take_percent:.2f}%")
                
                # ПРИНИМАЕМ РЕШЕНИЕ ПО ПРОЦЕНТАМ!
                self._check_exit_conditions(symbol, pnl_percent)
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    def _check_exit_conditions(self, symbol: str, pnl_percent: float):
        pos = self.positions.get(symbol)
        if not pos:
            return
        
        should_close = False
        reason = ""

        """"

        if pnl_percent >= 0.2:
            # Проверяем, не активирован ли уже трейлинг
            if not hasattr(pos, 'trailing_activated') or not pos.trailing_activated:
                pos.trailing_activated = True
                print(f"   🔄 {symbol}: трейлинг 0.3% активирован (PnL {pnl_percent:.2f}%)")
                
                # Рассчитываем новый стоп (цена входа = безубыток)
                new_stop = pos.entry_price
                
                # Отправляем в трейдер на обновление
                threading.Thread(
                    target=self.trader.update_stops,
                    args=(symbol, new_stop, None),
                    daemon=True
                ).start()

            # Уровень 2: при 0.5% - стоп на 0.3% прибыли
            if pnl_percent >= 0.3:
                if not hasattr(pos, 'trailing_activated_05') or not pos.trailing_activated_05:
                    pos.trailing_activated_05 = True
                    print(f"   🔄 {symbol}: трейлинг 0.5% активирован (PnL {pnl_percent:.2f}%)")
                    
                    # Рассчитываем цену для стопа (0.3% прибыли)
                    if pos.side == "BUY":
                        # Для LONG: стоп на цене, которая дает +0.3%
                        new_stop = pos.entry_price * (1 + 0.25/100)
                    else:
                        # Для SHORT: стоп на цене, которая дает +0.3%
                        new_stop = pos.entry_price * (1 - 0.25/100)
                    
                    threading.Thread(
                        target=self.trader.update_stops,
                        args=(symbol, new_stop, None),
                        daemon=True
                    ).start()

        """
        
        # Для LONG позиции
        if pos.side == "BUY":
            if pnl_percent <= -pos.stop_percent:
                should_close = True
                reason = "STOP_LOSS"
                print(f"   🛑 {symbol}: СТОП-ЛОСС! PnL {pnl_percent:.2f}% <= -{pos.stop_percent}%")
            elif pnl_percent >= pos.take_percent:
                should_close = True
                reason = "TAKE_PROFIT"
                print(f"   🎯 {symbol}: ТЕЙК-ПРОФИТ! PnL {pnl_percent:.2f}% >= {pos.take_percent}%")
        
        # Для SHORT позиции
        else:
            if pnl_percent <= -pos.stop_percent:
                should_close = True
                reason = "STOP_LOSS"
                print(f"   🛑 {symbol}: СТОП-ЛОСС SHORT! PnL {pnl_percent:.2f}% <= -{pos.stop_percent}%")
            elif pnl_percent >= pos.take_percent:
                should_close = True
                reason = "TAKE_PROFIT"
                print(f"   🎯 {symbol}: ТЕЙК-ПРОФИТ SHORT! PnL {pnl_percent:.2f}% >= {pos.take_percent}%")
        
        if should_close:
            def close_and_record():
                try:
                    # Сохраняем данные позиции
                    pos_data = {
                        'side': pos.side,
                        'entry_price': pos.entry_price,
                        'quantity': pos.quantity,
                        'entry_time': pos.entry_time.isoformat() if hasattr(pos.entry_time, 'isoformat') else str(pos.entry_time),
                        'stop_percent': pos.stop_percent,
                        'take_percent': pos.take_percent
                    }
                    
                    # Получаем цену и PnL перед закрытием
                    positions = self.trader.get_positions(symbol)
                    exit_price = 0
                    realized_pnl = 0
                    
                    if positions:
                        exit_price = float(positions[0].get('markPrice', 0))
                        realized_pnl = float(positions[0].get('unrealizedProfit', 0))
                    
                    # Закрываем позицию
                    result = self.trader.close_position(symbol)
                    
                    # Если есть оркестратор - сообщаем о закрытии
                    if result and self.orchestrator:
                        self.orchestrator.record_closed_position(
                            symbol=symbol,
                            exit_price=exit_price,
                            realized_pnl=realized_pnl,
                            pnl_percent=pnl_percent,
                            exit_reason=reason,
                            pos_data=pos_data
                        )
                    
                    # Удаляем из монитора
                    if symbol in self.positions:
                        del self.positions[symbol]
                        
                except Exception as e:
                    print(f"   ❌ Ошибка при закрытии {symbol}: {e}")
            
            threading.Thread(target=close_and_record, daemon=True).start()
    
    def run_monitoring(self, interval: int = 5):
        """Запуск мониторинга"""
        print(f"\n🚀 МОНИТОРИНГ ЗАПУЩЕН (интервал {interval}с)")
        print(f"   Решения принимаются по процентному PnL с биржи")
        
        try:
            while True:
                self.sync_positions()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Мониторинг остановлен")


if __name__ == "__main__":
    from bx_trader import BingXTrader
    from bx_api import BingXAPI
    
    logging.basicConfig(level=logging.INFO)
    
    api = BingXAPI()
    trader = BingXTrader(api)
    monitor = BxMonitor(trader)
    
    # Пример добавления позиции
    # monitor.add_position("BTC-USDT", "BUY", 50000, 0.001, 2.5, 5.0)
    
    monitor.run_monitoring()