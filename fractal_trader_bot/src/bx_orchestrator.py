# bx_orchestrator.py
import time
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

# НОВЫЕ ИМПОРТЫ
from bx_api import BingXAPI
from bx_trader import BingXTrader
from bx_monitor import BxMonitor
from bx_risk_manager import RiskManager
from bx_signal_parser import BingXOrderPreparer
from SIMULATOR import analyze_and_record 
from config_loader import config
from positionSizing import positionSizing
from bx_db_writer import get_db_writer, DBWriterContext

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('BxOrchestrator')

# Подавляем только технические логи
logging.getLogger('api_requests').setLevel(logging.CRITICAL)

class BxOrchestrator:
    def __init__(self):
        print("\n" + "="*60)
        print("ЗАПУСК ТОРГОВОЙ СИСТЕМЫ")
        print("="*60)
        
        # 1. СОЗДАЕМ API КЛИЕНТ
        self.api = BingXAPI()
        
        # 2. СОЗДАЕМ ТРЕЙДЕРА С API
        self.trader = BingXTrader(self.api)
        
        # 3. ПОЛУЧАЕМ БАЛАНС
        try:
            balance = self.trader.get_balance(force_refresh=True)
            print(f"💰 Баланс: {balance:.2f} {self.api.base_currency}")
        except Exception as e:
            print(f"⚠️ Ошибка баланса: {e}")
            balance = 1000.0
        
        # 4. СОЗДАЕМ МОНИТОР
        self.monitor = BxMonitor(self.trader, orchestrator=self)
        
        # 5. РИСК-МЕНЕДЖЕР
        self.risk_manager = RiskManager()
        self.risk_manager.update_balance(balance)
        
        # 6. ПОЗИШН-САЙЗИНГ (НОВЫЙ!)
        self.sizing = positionSizing()
        
        # 7. НАСТРОЙКИ
        self.max_positions = self.risk_manager.config.get('max_positions', 3)
        self.parser = BingXOrderPreparer()
        
        print(f"🌐 Режим: {'ТЕСТНЕТ' if config.testnet else 'РЕАЛ'}")
        print(f"📊 Макс позиций: {self.max_positions}")
        print("="*60)
        
        self.running = True
        self.cycle_count = 0
        self.total_trades = 0

        # 8. ИНИЦИАЛИЗАЦИЯ DB
        try:
            self.db_writer = get_db_writer('positions.db')
            print(f"💾 База данных: positions.db")
            
            # Проверяем открытые позиции при старте
            open_positions = self.db_writer.get_open_positions()
            if open_positions:
                print(f"📂 Найдено открытых позиций в БД: {len(open_positions)}")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации БД: {e}")
            self.db_writer = None
    
    def execute_trades(self, prepared_orders: List[Dict]) -> int:
        """Исполняет подготовленные ордера"""
        if not prepared_orders:
            return 0
        
        # Фильтруем уже открытые позиции
        active_symbols = set(self.monitor.positions.keys())
        available_slots = self.max_positions - len(active_symbols)
        
        if available_slots <= 0:
            print(f"\n⏳ Нет свободных слотов ({len(active_symbols)}/{self.max_positions})")
            return 0
        
        print(f"\n📨 Исполнение ордеров (слотов: {available_slots}):")
        
        executed = 0
        for idx, prepared in enumerate(prepared_orders[:available_slots], 1):
            symbol = prepared['original_symbol']
            direction = prepared['direction']
            
            # БЕРЕМ ДАННЫЕ ИЗ ПОДГОТОВЛЕННОГО ОРДЕРА
            summary = prepared['summary']
            qty = summary['quantity']
            price = summary['entry_price']
            
            # ЭТАЛОННЫЕ ПРОЦЕНТЫ УЖЕ ЕСТЬ В summary!
            stop_percent = summary['stop_percent'] 
            take_percent = summary['take_percent']
            atr_pct = summary.get('atr_pct', 0)
            
            print(f"\n{idx}. {symbol} ({direction}) {qty:.4f} @ {price:.4f}")
            if atr_pct > 0:
                print(f"   📊 ATR: {atr_pct:.2f}% | Стоп: {stop_percent:.2f}% | Тейк: {take_percent:.2f}%")
            
            # === ПРОВЕРКИ ===
            
            # 1. Проверка глобальных лимитов
            can_trade, reason = self.risk_manager.can_trade(self.monitor)
            if not can_trade:
                print(f"   → ⚠️ {reason}")
                continue
            
            # 2. Проверка на дублирование
            if symbol in self.monitor.positions:
                print(f"   → ⚠️ Уже открыта")
                continue
            
            # 3. Проверка R/R (уже есть в summary)
            rr = summary.get('risk_reward_ratio', 0)
            ok, reason = self.risk_manager.check_rr(rr)
            if not ok:
                print(f"   → ⚠️ {reason}")
                continue
            
            # === ОТКРЫТИЕ ПОЗИЦИИ ===
            try:
                # Определяем сторону для трейдера
                side = 'BUY' if direction == 'UP' else 'SELL'
                
                # === ДОБАВЬ ЭТОТ БЛОК ===
                # Получаем актуальную цену с биржи
                current_price = self.trader.get_current_price(symbol)
                if not current_price:
                    print(f"   ❌ Не удалось получить текущую цену для {symbol}")
                    continue
                
                print(f"   📈 Цена в сигнале: {price:.4f} | Текущая: {current_price:.4f}")
                
                # Пересчитываем количество по текущей цене (чтобы сохранить риск в USDT)
                position_value_usdt = 5.5  # из конфига
                new_qty = position_value_usdt / current_price
                
                # Проверяем минимальное количество
                min_qty = self.trader.api.get_min_qty(symbol)
                if new_qty < min_qty:
                    new_qty = min_qty
                    print(f"   ⚠️ Количество увеличено до {min_qty} (мин)")
                
                # Рассчитываем стоп/тейк от ТЕКУЩЕЙ цены
                if direction == "UP":
                    stop_price = current_price * (1 - stop_percent/100)
                    take_price = current_price * (1 + take_percent/100)
                else:  # DOWN
                    stop_price = current_price * (1 + stop_percent/100)
                    take_price = current_price * (1 - take_percent/100)
                
                print(f"   🎯 Стоп: {stop_price:.6f} | Тейк: {take_price:.6f}")
                
                # Открываем с новым методом (используем new_qty вместо qty)
                result = self.trader.open_position_with_stops(
                    symbol=symbol,
                    side=side,
                    quantity=new_qty,
                    stop_loss_price=stop_price,
                    take_profit_price=take_price
                )
                
                if result and result.get('order_id'):
                    order_id = result['order_id']
                    
                    # РЕГИСТРИРУЕМ В МОНИТОРЕ (используем current_price вместо price)
                    self.monitor.add_position(
                        symbol=symbol,
                        side=side,
                        entry_price=current_price,  # ← ТЕКУЩАЯ ЦЕНА!
                        quantity=new_qty,           # ← ПЕРЕСЧИТАННОЕ!
                        stop_percent=stop_percent,
                        take_percent=take_percent
                    )

                    # ЗАПИСЫВАЕМ В БД (тоже с текущими значениями)
                    if self.db_writer:
                        self.db_writer.add_position(
                            symbol=symbol,
                            side=side,
                            entry_price=current_price,  # ← ТЕКУЩАЯ ЦЕНА!
                            quantity=new_qty,           # ← ПЕРЕСЧИТАННОЕ!
                            stop_percent=stop_percent,
                            take_percent=take_percent,
                            metadata={
                                'order_id': order_id,
                                'atr_pct': atr_pct,
                                'risk_reward': rr,
                                'direction': direction,
                                'signal_price': price  # сохраняем для истории
                            }
                        )
                    
                    print(f"   ✅ ID: {order_id} | Позиция открыта")
                    executed += 1
                    self.total_trades += 1
                    
                    # Обновляем баланс
                    new_balance = self.trader.get_balance(force_refresh=True)
                    self.risk_manager.update_balance(new_balance)
                    
                else:
                    print(f"   ❌ Ошибка открытия")
                    
            except Exception as e:
                print(f"   ❌ {str(e)[:100]}")
            
            time.sleep(1)
        
        return executed
    
    
    def record_closed_position(self, symbol: str, exit_price: float, 
                          realized_pnl: float, pnl_percent: float, 
                          exit_reason: str, pos_data: dict):
        if not self.db_writer:
            return
        
        self.db_writer.update_position(
            symbol=symbol,
            exit_price=exit_price,
            realized_pnl=realized_pnl,
            realized_pnl_percent=pnl_percent,
            exit_reason=exit_reason,
            metadata=pos_data
        )

    def run_cycle(self):
        """Полный торговый цикл"""
        self.cycle_count += 1
        print(f"\n{'='*70}")
        print(f"ЦИКЛ #{self.cycle_count} [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"{'='*70}")
        
        # 1. МОНИТОРИНГ ТЕКУЩИХ ПОЗИЦИЙ
        print("\n📊 МОНИТОРИНГ ПОЗИЦИЙ")
        self.monitor.sync_positions()
        
        # Получаем сводку по открытым позициям
        active_positions = len(self.monitor.positions)
        if active_positions > 0:
            print(f"   Активных позиций: {active_positions}")
        else:
            print("   Нет открытых позиций")
        
        # 2. ПРОВЕРКА РИСКОВ
        print("\n⚖️ ПРОВЕРКА РИСКОВ")
        can_trade, reason = self.risk_manager.can_trade(self.monitor)
        if not can_trade:
            print(f"   ⏸️ {reason}")
            return
        else:
            print(f"   ✅ Можно торговать (слотов: {self.max_positions - active_positions})")
        
        # 3. ПОИСК НОВЫХ СИГНАЛОВ
        print("\n🔍 ПОИСК НОВЫХ СИГНАЛОВ")
        
        # Получаем текущий баланс
        balance = self.trader.get_balance()
        
        signals = analyze_and_record(
            capital=balance, 
            max_positions=self.max_positions - active_positions
        )
        
        if not signals:
            print("   Сигналов нет")
            return
        
        print(f"   Найдено сигналов: {len(signals)}")
        
        # Подготавливаем ордера
        prepared = self.parser.prepare_signals(signals)
        if not prepared:
            print("   Нет ордеров для исполнения")
            return
        
        print(f"   Подготовлено ордеров: {len(prepared)}")
        
        # Исполняем
        executed = self.execute_trades(prepared)
        
        # 4. ИТОГИ ЦИКЛА
        print(f"\n{'='*70}")
        print(f"ИТОГИ ЦИКЛА #{self.cycle_count}")
        print(f"📈 Открыто позиций: {executed}/{len(prepared)}")
        print(f"📊 Всего сделок: {self.total_trades}")
        print(f"💰 Текущий баланс: {self.trader.get_balance():.2f} {self.api.base_currency}")
        print(f"{'='*70}")
    
    def run(self):
        """Запуск оркестратора"""
        scan_interval = config.scan_interval
        monitor_interval = config.monitor_interval
        
        print(f"\n⏱️ Сканирование: {scan_interval//60} мин")
        print(f"⏱️ Мониторинг: {monitor_interval} сек")
        print("="*60)
        
        # Первый цикл сразу при запуске
        self.run_cycle()
        
        last_scan = time.time()
        last_monitor = time.time()
        
        try:
            while self.running:
                now = time.time()
                
                # Мониторинг позиций (часто)
                if now - last_monitor >= monitor_interval:
                    print(f"\n🔄 Мониторинг...")
                    self.monitor.sync_positions()
                    last_monitor = now
                
                # Полный цикл (редко)
                if now - last_scan >= scan_interval:
                    self.run_cycle()
                    last_scan = now
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n" + "="*70)
            print("🛑 ОСТАНОВКА ПОЛЬЗОВАТЕЛЕМ")
            print("="*70)

             # Закрываем соединение с БД (НОВОЕ!)
            if hasattr(self, 'db_writer') and self.db_writer:
                self.db_writer.close()
            
            # Финальный отчет
            print(f"\n📊 Статистика:")
            print(f"   Всего сделок: {self.total_trades}")
            print(f"   Баланс: {self.trader.get_balance():.2f} {self.api.base_currency}")
            
            # Показываем открытые позиции
            if self.monitor.positions:
                print(f"\n📌 Открытые позиции ({len(self.monitor.positions)}):")
                for symbol, pos in self.monitor.positions.items():
                    print(f"   {symbol}: {pos.side}, стоп {pos.stop_percent}%, тейк {pos.take_percent}%")
            
            print("="*70)

if __name__ == "__main__":
    BxOrchestrator().run()