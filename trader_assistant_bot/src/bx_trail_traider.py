# bx_trail_traider.py - ФИНАЛЬНАЯ ВЕРСИЯ
import time
import json
import os
import requests
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
from bx_trader import BingXTrader
from bx_api import BingXAPI
from bx_fractal import FractalFinder

@dataclass
class Position:
    symbol: str
    side: str
    entry_price: float
    quantity: float
    current_stop: float
    best_price: float
    trailing_activated: bool
    last_atr_update: float
    last_fractal_update: float = 0.0
    manual_mode: bool = False 
    breakeven_notified: bool = False  
    


class ATRTrailingMonitor:
    def __init__(self, trader, atr_timeframe: str = "1h", atr_period: int = 14, stop_mult: float = 3.0):
        self.trader = trader
        self.atr_timeframe = atr_timeframe
        self.atr_period = atr_period
        self.stop_mult = stop_mult
        self.fractal_finder = FractalFinder(timeframe="15m", lookback=100)
        
        self.positions = {}
        self.db_file = "atr_positions.json"
        self.atr_update_interval = 3600
        
        self.load_positions()
        
        print(f"\n{'='*60}")
        print(f"🚀 ATR TRAILING STOP MONITOR")
        print(f"{'='*60}")
        print(f"   📈 ATR таймфрейм: {atr_timeframe}")
        print(f"   🛑 Стоп: {stop_mult} × ATR")
        print(f"   ⏱️  Обновление стопов: при движении цены + раз в 15 минут")
        print(f"   🎯 Активация трейлинга: +0.2%")
        print(f"{'='*60}\n")
    
    def load_positions(self):
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    for symbol, pos_data in data.items():
                        self.positions[symbol] = Position(**pos_data)
                print(f"📁 Загружено {len(self.positions)} позиций")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки: {e}")
    
    def save_positions(self):
        try:
            data = {}
            for symbol, pos in self.positions.items():
                data[symbol] = {
                    'symbol': pos.symbol,
                    'side': pos.side,
                    'entry_price': pos.entry_price,
                    'quantity': pos.quantity,
                    'current_stop': pos.current_stop,
                    'best_price': pos.best_price,
                    'trailing_activated': pos.trailing_activated,
                    'manual_mode': pos.manual_mode,
                    'last_atr_update': pos.last_atr_update,
                    'breakeven_notified': pos.breakeven_notified,
                    'last_fractal_update': pos.last_fractal_update
                }
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения: {e}")
    
    def get_klines(self, symbol: str, limit: int = 50) -> Optional[List[Dict]]:
        try:
            url = "https://open-api-vst.bingx.com/openApi/swap/v3/quote/klines"
            params = {
                'symbol': symbol,
                'interval': self.atr_timeframe,
                'limit': limit
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data'):
                    candles = []
                    for item in data['data']:
                        if isinstance(item, dict):
                            candles.append({
                                'high': float(item['high']),
                                'low': float(item['low']),
                                'close': float(item['close'])
                            })
                    return candles if len(candles) >= 15 else None
        except Exception as e:
            print(f"   ⚠️ Ошибка свечей {symbol}: {e}")
        return None
    
    def calculate_atr(self, symbol: str) -> Optional[float]:
        try:
            klines = self.get_klines(symbol, 50)
            if not klines or len(klines) < self.atr_period + 1:
                return None
            
            tr_values = []
            for i in range(1, len(klines)):
                tr = max(
                    klines[i]['high'] - klines[i]['low'],
                    abs(klines[i]['high'] - klines[i-1]['close']),
                    abs(klines[i]['low'] - klines[i-1]['close'])
                )
                tr_values.append(tr)
            
            if len(tr_values) >= self.atr_period:
                atr = sum(tr_values[:self.atr_period]) / self.atr_period
                for tr in tr_values[self.atr_period:]:
                    atr = (atr * (self.atr_period - 1) + tr) / self.atr_period
                return atr
        except Exception as e:
            print(f"   ⚠️ Ошибка ATR {symbol}: {e}")
        return None
    
    def place_stop_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> bool:
        """Прямая установка стоп-лосс ордера через API"""
        try:
            if side == "BUY":
                close_side = "SELL"
                position_side = "LONG"
            else:
                close_side = "BUY"
                position_side = "SHORT"
            
            params = {
                'symbol': symbol,
                'side': close_side,
                'positionSide': position_side,
                'type': 'STOP_MARKET',
                'quantity': str(quantity),
                'stopPrice': str(stop_price),
                'workingType': 'MARK_PRICE',
                'newClientOrderId': f"atr_stop_{int(time.time())}"
            }
            
            result = self.trader.api.request('POST', self.trader.api.endpoints['order'], params)
            
            if result:
                print(f"   ✅ Стоп {symbol}: ${stop_price:.4f}")
                return True
            return False
        except Exception as e:
            print(f"   ❌ Ошибка стопа {symbol}: {e}")
            return False
    
    def initialize_stops(self):
        """При запуске - устанавливаем стопы для всех позиций из БД"""
        if not self.positions:
            return
        
        print(f"\n🔧 УСТАНОВКА СТОПОВ ПРИ ЗАПУСКЕ")
        for symbol, pos in self.positions.items():
            print(f"   📍 {symbol}: стоп ${pos.current_stop:.4f}")
            self.place_stop_order(symbol, pos.side, pos.quantity, pos.current_stop)
            time.sleep(0.5)
        print(f"✅ Готово\n")
    
    def sync_all_positions(self):
        """Синхронизация - обновляем данные с биржи и пересчитываем стопы"""
        print(f"\n🔄 СИНХРОНИЗАЦИЯ [{datetime.now().strftime('%H:%M:%S')}]")
        
        try:
            exchange_positions = self.trader.get_positions()
            
            if not exchange_positions:
                if self.positions:
                    print("   Нет открытых позиций на бирже")
                return
            
            current_positions = {}
            for pos_data in exchange_positions:
                position_amt = float(pos_data.get('positionAmt', 0))
                if position_amt != 0:
                    symbol = pos_data.get('symbol')
                    side = 'BUY' if pos_data.get('positionSide') == 'LONG' else 'SELL'
                    entry_price = float(pos_data.get('avgPrice', pos_data.get('entryPrice', 0)))
                    if entry_price == 0:
                        entry_price = float(pos_data.get('markPrice', 0))
                    quantity = abs(position_amt)
                    mark_price = float(pos_data.get('markPrice', 0))
                    pnl_pct = float(pos_data.get('pnlRatio', 0)) * 100
                    
                    current_positions[symbol] = {
                        'side': side,
                        'entry_price': entry_price,
                        'quantity': quantity,
                        'mark_price': mark_price,
                        'pnl_pct': pnl_pct
                    }
            
            for symbol, pos_info in current_positions.items():
                current_price = pos_info['mark_price']
                pnl_pct = pos_info['pnl_pct']
                entry_price = pos_info['entry_price']
                quantity = pos_info['quantity']
                side = pos_info['side']
                
                # НОВАЯ ПОЗИЦИЯ
                if symbol not in self.positions:
                    print(f"\n   ➕ НОВАЯ ПОЗИЦИЯ: {symbol}")
                    print(f"      Сторона: {side}")
                    print(f"      Цена входа: ${entry_price:.4f}")
                    print(f"      Кол-во: {quantity}")
                    
                    atr = self.calculate_atr(symbol)
                    if atr:
                        atr_pct = (atr / entry_price) * 100
                        if side == 'BUY':
                            stop_price = entry_price - (atr * self.stop_mult)
                        else:
                            stop_price = entry_price + (atr * self.stop_mult)
                        stop_price = round(stop_price, 4)
                        print(f"      ATR: ${atr:.4f} ({atr_pct:.2f}%)")
                        print(f"      Нач. стоп: ${stop_price}")
                    else:
                        if side == 'BUY':
                            stop_price = round(entry_price * 0.985, 4)
                        else:
                            stop_price = round(entry_price * 1.015, 4)
                        print(f"      ⚠️ ATR не получен, стоп 1.5%")

                    manual_mode = False
                    breakeven_notified = False
                    
                    if side == "BUY" and stop_price >= entry_price * 1.001:
                        manual_mode = True
                        breakeven_notified = True
                        print(f"      ℹ️ Стоп уже в безубытке, переключаю в ручной режим")
                    elif side == "SELL" and stop_price <= entry_price * 0.999:
                        manual_mode = True
                        breakeven_notified = True
                        print(f"      ℹ️ Стоп уже в безубытке, переключаю в ручной режим")    
                    
                    pos = Position(
                        symbol=symbol,
                        side=side,
                        entry_price=entry_price,
                        quantity=quantity,
                        current_stop=stop_price,
                        best_price=entry_price,
                        last_atr_update=time.time(),
                        trailing_activated=False,
                        manual_mode=manual_mode,
                        breakeven_notified=breakeven_notified
                    )
                    self.positions[symbol] = pos
                    self.place_stop_order(symbol, side, quantity, stop_price)
                    self.save_positions()
                
                # СУЩЕСТВУЮЩАЯ ПОЗИЦИЯ
                else:
                    pos = self.positions[symbol]
                    
                    # Обновляем лучшую цену (только для LONG)
                    if side == "BUY" and current_price > pos.best_price:
                        pos.best_price = current_price
                        print(f"   📈 {symbol}: новая лучшая цена ${pos.best_price:.4f}")
                    elif side == "SELL" and current_price < pos.best_price:
                        pos.best_price = current_price
                        print(f"   📉 {symbol}: новая лучшая цена ${pos.best_price:.4f}")    

                    # === ПРОВЕРКА ПО РЕАЛЬНЫМ ДАННЫМ С БИРЖИ ===
                    # Если стоп уже в безубытке (или выше для LONG, или ниже для SHORT) - включаем режим фракталов
                    if not pos.manual_mode:
                        if side == "BUY" and pos.current_stop >= entry_price:
                            pos.manual_mode = True
                            pos.breakeven_notified = True
                            print(f"   🔔 {symbol}: Стоп в безубытке (${pos.current_stop:.4f} >= ${entry_price:.4f}) - режим фракталов")
                            
                            # Сразу устанавливаем фрактальный стоп
                            fractal_stop = self.fractal_finder.get_fractal_stop_with_buffer(
                                symbol, current_price, side, buffer_pct=0.1
                            )
                            if fractal_stop:
                                if self.place_stop_order(symbol, side, quantity, fractal_stop):
                                    pos.current_stop = fractal_stop
                                    print(f"   ✅ Фрактальный стоп установлен: ${fractal_stop:.4f}")
                            else:
                                print(f"   ⚠️ Фрактал не найден, оставляю текущий стоп: ${pos.current_stop:.4f}")
                            
                            self.save_positions()
                            
                        elif side == "SELL" and pos.current_stop <= entry_price:
                            pos.manual_mode = True
                            pos.breakeven_notified = True
                            print(f"   🔔 {symbol}: Стоп в безубытке (${pos.current_stop:.4f} <= ${entry_price:.4f}) - режим фракталов")
                            
                            fractal_stop = self.fractal_finder.get_fractal_stop_with_buffer(
                                symbol, current_price, side, buffer_pct=0.1
                            )
                            if fractal_stop:
                                if self.place_stop_order(symbol, side, quantity, fractal_stop):
                                    pos.current_stop = fractal_stop
                                    print(f"   ✅ Фрактальный стоп установлен: ${fractal_stop:.4f}")
                            else:
                                print(f"   ⚠️ Фрактал не найден, оставляю текущий стоп: ${pos.current_stop:.4f}")
                            
                            self.save_positions()    
                    
                    # Активация трейлинга
                    if not pos.trailing_activated and pnl_pct >= 0.2:
                        pos.trailing_activated = True
                        print(f"   🎯 {symbol}: ТРЕЙЛИНГ АКТИВИРОВАН! (PnL {pnl_pct:.2f}%)")

                    # Пересчет стопа (при обновлении цены ИЛИ раз в 15 минут)
                    now = time.time()
                    need_update = False
                    
                    # Если цена обновилась - пересчитываем сразу
                    if side == "BUY" and current_price > pos.best_price:
                        need_update = True
                    elif side == "SELL" and current_price < pos.best_price:  # ← ДОБАВИТЬ
                        need_update = True
                    elif now - pos.last_atr_update >= self.atr_update_interval:
                        need_update = True

                    if need_update and not pos.manual_mode:
                        atr = self.calculate_atr(symbol)
                        if atr:
                            stop_distance = atr * self.stop_mult
                            
                            if side == "BUY":
                                new_stop = pos.best_price - stop_distance
                                if pos.trailing_activated:
                                    new_stop = max(new_stop, entry_price)
                                breakeven = entry_price * 1.001
                                new_stop = min(new_stop, breakeven)
                                new_stop = max(new_stop, entry_price)
                            else:  # SHORT
                                new_stop = pos.best_price + stop_distance
                                if pos.trailing_activated:
                                    new_stop = max(new_stop, entry_price)
                                breakeven = entry_price * 0.999
                                new_stop = max(new_stop, breakeven)
                            
                            new_stop = round(new_stop, 4)
                            
                            # Проверка безубытка
                            if not pos.breakeven_notified and not pos.manual_mode:
                                if side == "BUY" and new_stop >= breakeven:
                                    pos.breakeven_notified = True
                                    pos.manual_mode = True
                                    print(f"\n🔔 {symbol}: ДОСТИГНУТ БЕЗУБЫТОК! РУЧНОЙ РЕЖИМ")
                                    
                                    # === УСТАНОВКА СТОПА ПО ФРАКТАЛАМ ===
                                    fractal_stop = self.fractal_finder.get_fractal_stop_with_buffer(
                                        symbol, current_price, side, buffer_pct=0.1
                                    )
                                    
                                    if fractal_stop:
                                        print(f"   📊 Найден фрактальный стоп: ${fractal_stop:.4f}")
                                        if self.place_stop_order(symbol, side, quantity, fractal_stop):
                                            pos.current_stop = fractal_stop
                                            print(f"   ✅ Стоп по фракталу установлен: ${fractal_stop:.4f}")
                                    else:
                                        print(f"   ⚠️ Фрактал не найден, оставляю текущий стоп: ${pos.current_stop:.4f}")
                                    
                                elif side == "SELL" and new_stop <= breakeven:
                                    pos.breakeven_notified = True
                                    pos.manual_mode = True
                                    print(f"\n🔔 {symbol}: ДОСТИГНУТ БЕЗУБЫТОК! РУЧНОЙ РЕЖИМ")
                                    
                                    # === УСТАНОВКА СТОПА ПО ФРАКТАЛАМ ===
                                    fractal_stop = self.fractal_finder.get_fractal_stop_with_buffer(
                                        symbol, current_price, side, buffer_pct=0.1
                                    )
                                    
                                    if fractal_stop:
                                        print(f"   📊 Найден фрактальный стоп: ${fractal_stop:.4f}")
                                        if self.place_stop_order(symbol, side, quantity, fractal_stop):
                                            pos.current_stop = fractal_stop
                                            print(f"   ✅ Стоп по фракталу установлен: ${fractal_stop:.4f}")
                                    else:
                                        print(f"   ⚠️ Фрактал не найден, оставляю текущий стоп: ${pos.current_stop:.4f}")
                            
                            # Обновляем стоп если изменился
                            if abs(new_stop - pos.current_stop) > 0.001:
                                if self.place_stop_order(symbol, side, quantity, new_stop):
                                    pos.current_stop = new_stop
                                    print(f"   🔄 {symbol}: стоп обновлен → ${new_stop:.4f}")
                        
                        
                        self.save_positions()

                    # === ПЕРЕСЧЕТ ФРАКТАЛОВ В РУЧНОМ РЕЖИМЕ (каждые 5 минут) ===
                    if pos.manual_mode:
                        fractal_now = time.time()
                        
                        if fractal_now - pos.last_fractal_update >= 25:
                            # Получаем все фракталы для отладки
                            all_fractals = self.fractal_finder.find_fractals(symbol)
                            fractal_stop = self.fractal_finder.get_fractal_stop_with_buffer(
                                symbol, current_price, side, buffer_pct=0.05
                            )
                            
                            if fractal_stop and abs(fractal_stop - pos.current_stop) > 0.001:
                                if self.place_stop_order(symbol, side, quantity, fractal_stop):
                                    pos.current_stop = fractal_stop
                                    print(f"   ✅ {symbol}: фрактальный стоп обновлен → ${fractal_stop:.4f}")
                            else:
                                if not fractal_stop:
                                    print(f"   ⚠️ Фрактал не найден")
                            
                            pos.last_fractal_update = fractal_now
                            self.save_positions()
                    
                    # ВЫВОД
                    arrow = "🟢" if side == "BUY" else "🔴"
                    mode = "999 ФРАКТАЛ" if pos.manual_mode else "🤖 АВТО"
                    pnl_color = "🟢" if pnl_pct >= 0 else "🔴"
                    
                    if side == "BUY":
                        stop_pct = ((current_price - pos.current_stop) / current_price) * 100 if current_price > pos.current_stop else 0
                    else:
                        stop_pct = ((pos.current_stop - current_price) / current_price) * 100 if pos.current_stop > current_price else 0
                    
                    print(f"\n   {arrow} {symbol} [{mode}]")
                    print(f"      💰 Цена: ${current_price:.4f} | PnL: {pnl_color}{pnl_pct:+.2f}%")
                    print(f"      📈 Вход: ${entry_price:.4f} | Лучшая: ${pos.best_price:.4f}")
                    print(f"      🛑 Стоп: ${pos.current_stop:.4f} ({stop_pct:.2f}% от цены)")
                    
                    # ПРОВЕРКА СТОПА
                    stop_triggered = (side == "BUY" and current_price <= pos.current_stop) or (side == "SELL" and current_price >= pos.current_stop)

                    if stop_triggered:
                        print(f"   🛑 {symbol}: СТОП СРАБОТАЛ!")
                        
                        if symbol == "BTC-USDT":
                            for alt_symbol in list(self.positions.keys()):
                                if alt_symbol != "BTC-USDT":
                                    print(f"   🔄 BTC стоп, закрываю {alt_symbol}")
                                    self.trader.close_position(alt_symbol)
                                    del self.positions[alt_symbol]
                        
                        del self.positions[symbol]
                        self.save_positions()
                        continue  # пропускаем остальную обработку этой позиции
            
            # Удаляем позиции, которых нет на бирже
            for symbol in list(self.positions.keys()):
                if symbol not in current_positions:
                    print(f"\n   ❌ {symbol}: позиция закрыта")
                    del self.positions[symbol]
                    self.save_positions()
                    
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

    def clear_db_on_start(self):
        """Очищает БД при запуске - удаляет все позиции из файла"""
        if os.path.exists(self.db_file):
            try:
                os.remove(self.db_file)
            except Exception as e:
                print(f"⚠️ Ошибка удаления БД: {e}")
        
        # Очищаем словарь позиций в памяти
        self.positions = {}
        print(f"✅ Состояние очищено, начинаем с нуля")        
    
    def run(self, interval: int = 25):
        print("🚀 МОНИТОРИНГ ЗАПУЩЕН")
        print(f"   🔁 Интервал: {interval} сек\n")
        
        # self.clear_db_on_start()
        # При запуске - устанавливаем стопы
        self.initialize_stops()
        
        try:
            while True:
                self.sync_all_positions()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 ОСТАНОВЛЕН")
            self.save_positions()


if __name__ == "__main__":
    from bx_api import BingXAPI
    from bx_trader import BingXTrader
    
    api = BingXAPI()
    trader = BingXTrader(api, required_leverage=1)
    
    monitor = ATRTrailingMonitor(
        trader=trader,
        atr_timeframe="15m",
        atr_period=14,
        stop_mult=3.0
    )
    
    monitor.run(interval=25)