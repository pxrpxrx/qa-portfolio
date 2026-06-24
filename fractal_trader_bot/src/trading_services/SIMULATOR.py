# tradingSimulator.py
import logging
from datetime import datetime
import sys
import os
import concurrent.futures
import time
from pathlib import Path
import json

# Добавляем пути
sys.path.insert(0, str(Path(__file__).parent / "operators"))
sys.path.insert(0, str(Path(__file__).parent / "indicators"))

from FRACTAL_SIGNALS import analyze_symbol, get_all_symbols
from positionSizing import positionSizing

# ========== НАСТРОЙКИ ==========
TEST_MODE = False
TEST_LIMIT = 700
MAX_WORKERS = 20
BATCH_SIZE = 50
# ================================

# Отключаем логирование в консоль - только в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_simulator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('TradingSimulator')

def analyze_symbol_wrapper(symbol):
    """Обертка для анализа одного символа"""
    try:
        start = time.time()
        result = analyze_symbol(symbol)
        elapsed = time.time() - start
        if result:
            logger.debug(f"OK {symbol} за {elapsed:.2f}с")
        return result
    except Exception as e:
        logger.debug(f"ERR {symbol}: {e}")
        return None

def analyze_and_record(capital=10000, max_positions=25) -> list:

    all_symbols = get_all_symbols()
    symbols_to_analyze = all_symbols[:TEST_LIMIT] if TEST_MODE else all_symbols
    
    logger.info(f"Режим: {'ТЕСТ' if TEST_MODE else 'ПОЛНЫЙ'}, монет: {len(symbols_to_analyze)}")
    
    signals = []
    start_time = time.time()
    
    # Параллельный анализ символов
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_symbol = {executor.submit(analyze_symbol_wrapper, s): s 
                           for s in symbols_to_analyze}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_symbol), 1):
            result = future.result()
            if result and result.get('trend') in ['UP', 'DOWN'] and result.get('price', 0) > 0:
                signals.append(result)
            
            if i % 50 == 0:
                elapsed = time.time() - start_time
                logger.info(f"Прогресс: {i}/{len(symbols_to_analyze)} | Сигналов: {len(signals)} | {elapsed:.1f}с")
    
    elapsed = time.time() - start_time
    logger.info(f"Анализ завершен за {elapsed:.1f}с, сырых сигналов: {len(signals)}")
    
    if not signals:
        logger.info("❌ Сигналов не найдено")
        return []
    
    # 2. Фильтруем
    config_path = Path('risk_config.json')
    blacklist = []
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            risk_config = json.load(f)
            blacklist = risk_config.get('blacklist', [])
            min_atr_percent = risk_config.get('min_atr_percent', 0.255)
    else:
        min_atr_percent = 0.255
    
    signals_with_data = []
    capital_per_trade = capital 

    for signal in signals:
        symbol = signal.get('symbol', '')

        if symbol in blacklist:
            logger.debug(f"⏭️ {symbol}: в черном списке")
            continue

        try:
            pos = positionSizing(
                capital=capital_per_trade,
                price=signal['price'],
                atr=signal.get('atr'),
                direction=signal['trend'],
                target_position_usdt=5.5
            )
            if pos and pos.get('size', 0) > 0:
                # Добавляем данные в сигнал
                signal['position_size'] = pos['size']
                signal['stop_loss'] = pos['stop_loss']
                signal['take_profit'] = pos['take_profit']
                signal['risk_reward_ratio'] = pos.get('risk_reward_ratio', 0)
                signal['stop_percent'] = pos.get('stop_percent', 0.4)
                signal['take_percent'] = pos.get('take_percent', 0.8)
                signal['expected_net_profit'] = pos.get('expected_net_profit', 0)
                signal['expected_net_loss'] = pos.get('expected_net_loss', 0)
                signals_with_data.append(signal)
        except Exception as e:
            logger.error(f"Ошибка расчета для {signal.get('symbol')}: {e}")
            continue

    filtered_signals = []
    for s in signals_with_data:

        # Рассчитываем ATR в процентах
        atr_pct = (s.get('atr', 0) / s['price']) * 100 if s.get('atr') else 0

        # Проверяем ТОЛЬКО ATR
        if atr_pct < min_atr_percent:
            logger.debug(f"❌ {s['symbol']}: ATR {atr_pct:.3f}% < {min_atr_percent}%")
            continue

        if atr_pct > 6:
            logger.debug(f"❌ {s['symbol']}: ATR {atr_pct:.3f}% > 6% (слишком волатильна)")
            continue

        # Если ATR прошел - добавляем
        s['atr_pct'] = atr_pct
        filtered_signals.append(s)

    # 3. Сортируем отфильтрованные по качеству
    filtered_signals.sort(key=lambda x: x.get('final', 0), reverse=True)

    # 4. Берем лучшие
    top_signals = filtered_signals[:max_positions]

    # 5. Создаем финальные сигналы (без пересчета!)
    prepared_signals = []
    for signal in top_signals:
        try:
            full_signal = {
                'symbol': signal['symbol'],
                'trend': signal['trend'],
                'direction': signal['trend'],
                'price': signal['price'],
                'entry_price': signal['price'],
                'position_size': signal['position_size'],  # ← уже посчитано!
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'atr': signal.get('atr', 0),
                'atr_pct': signal.get('atr_pct', 0),
                'stop_percent': signal.get('stop_percent', 0.4),
                'take_percent': signal.get('take_percent', 0.8),
                'stop_loss_pct': signal.get('stop_percent', 0.4),
                'take_profit_pct': signal.get('take_percent', 0.8),
                'risk_amount': signal.get('risk_amount', 0),
                'market_regime': signal.get('regime', 'UNKNOWN'),
                'regime_score': signal.get('regime_score', 0),
                'regime_adx': signal.get('regime_adx', 0),
                'regime_slope': signal.get('regime_slope', 0),
                'trend_score': signal.get('trend_score', 0),
                'trend_direction': signal.get('trend', 'UNKNOWN'),
                'confirmation': signal.get('confirmation', 0),
                'hurst': signal.get('hurst', 0.5),
                'momentum_score': signal.get('momentum', 0),
                'fractal_score': signal.get('fractal_score', 0),
                'fractal_signal': signal.get('fractal', 'NONE'),
                'volatility_score': signal.get('volatility', 0),
                'final_score': signal.get('final', 0),
                'atr_entry': signal.get('atr', 0),
                'signal_quality': signal.get('signal_quality', 'LOW'),
                'capital_used': capital_per_trade,
                'risk_reward_ratio': signal.get('risk_reward_ratio', 0),
                'position_value_usdt': signal['position_size'] * signal['price'],
                'expected_net_profit': signal.get('expected_net_profit', 0), 
                'expected_net_loss': signal.get('expected_net_loss', 0),     
            }
            print(f"   🔍 Расчет: {signal['position_size']} * {signal['price']} = {signal['position_size'] * signal['price']}")
            prepared_signals.append(full_signal)

            logger.info(f"{signal['symbol']}: {signal['trend']} @ {signal['price']:.4f} | "
                    f"Размер: {signal['position_size']:.4f} | "
                    f"Стоп: {signal.get('stop_percent', 0.4):.2f}% | "
                    f"Тейк: {signal.get('take_percent', 0.8):.2f}%")
        except Exception as e:
            logger.error(f"Ошибка обработки {signal.get('symbol')}: {e}")

    logger.info(f"📊 Подготовлено сигналов для исполнения: {len(prepared_signals)}/{len(top_signals)}")
    return prepared_signals

def show_trades(signals: list = None):
    """
    Отображение сигналов в консоли с процентами
    """
    print("\n" + "="*90)
    print("📊 ТЕКУЩИЕ СИГНАЛЫ")
    print("="*90)
    
    if not signals:
        print("Нет сигналов")
        print("="*90)
        return
    
    for idx, s in enumerate(signals, 1):
        arrow = "🟢" if s['trend'] == "UP" else "🔴"

        atr_pct = s.get('atr_pct', 0)

        print(f"{idx:2d}. {arrow} {s['symbol']:<12} | "
              f"Цена: {s['price']:<8.4f} | "
              f"Размер: {s['position_size']:<8.4f} | "
              f"Стоп: {s['stop_loss']:<8.4f} ({s.get('stop_percent', 0):.2f}%) | "
              f"Тейк: {s['take_profit']:<8.4f} ({s.get('take_percent', 0):.2f}%) | "
              f"**ATR: {atr_pct:.3f}%** | "
              f"Скор: {s['final_score']:.3f}")
        
                # ПОКАЗЫВАЕМ КОМПОНЕНТЫ
        print(f"     📊 Компоненты: Фрактал:{s.get('fractal_score', 0):+.3f} | "
              f"ADX:{s.get('adx', 0):.1f} | "
              f"Hurst:{s.get('hurst', 0):.2f} | "
              f"Подтв:{s.get('confirmation', 0):.1f} | "
              f"Режим:{s.get('market_regime', 'UNK')}")
    
    print("="*90)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Торговый симулятор')
    parser.add_argument('--capital', type=float, default=10000, help='Капитал для расчета')
    parser.add_argument('--max', type=int, default=5, help='Максимум сигналов')
    parser.add_argument('--show', action='store_true', help='Показать сигналы')
    parser.add_argument('--test', action='store_true', help='Тестовый режим')
    parser.add_argument('--limit', type=int, default=100, help='Лимит монет в тесте')
    parser.add_argument('--workers', type=int, default=20, help='Количество потоков')
    
    args = parser.parse_args()
    
    if args.test:
        TEST_MODE = True
        TEST_LIMIT = args.limit
        MAX_WORKERS = args.workers
        print(f"\n🧪 ТЕСТОВЫЙ РЕЖИМ: {TEST_LIMIT} монет, {MAX_WORKERS} потоков")
    
    if args.show:
        # Если только показать - берем из сохраненных? или просто заглушка
        print("Используйте без --show для получения сигналов")
    else:
        signals = analyze_and_record(capital=args.capital, max_positions=args.max)
        show_trades(signals)
        
        print(f"\n✅ Найдено сигналов: {len(signals)}")