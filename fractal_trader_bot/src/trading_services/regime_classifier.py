# regime_classifier.py
import sys
from pathlib import Path

# Добавляем путь к indicators
sys.path.insert(0, str(Path(__file__).parent / "indicators"))

# Импортируем индикаторы
from ema import calculate_ema
from adx import calculate_adx
from atr import calculate_atr
from operators.klineData_api import get_klines

def analyze_btc_regime():
    """
    Анализ рыночного режима по BTC-USDT
    """
    print("\n" + "="*70)
    print("📊 АНАЛИЗ РЫНОЧНОГО РЕЖИМА ПО BTC")
    print("="*70)
    
    try:
        # Получаем данные BTC
        print("📡 Запрос данных BTC-USDT...")
        btc_data = get_klines("BTC-USDT")
        
        if not btc_data or len(btc_data) < 200:
            print(f"❌ Недостаточно данных: {len(btc_data) if btc_data else 0} свечей")
            return None
        
        print(f"✅ Получено {len(btc_data)} свечей")
        
        # Конвертируем в нужный формат
        candles = []
        prices = []
        
        for d in btc_data:
            high = float(d['high'])
            low = float(d['low'])
            close = float(d['close'])
            candles.append((high, low, close))
            prices.append(close)
        
        print(f"📊 Первая свеча: High={candles[0][0]:.2f}, Low={candles[0][1]:.2f}, Close={candles[0][2]:.2f}")
        print(f"📊 Последняя свеча: High={candles[-1][0]:.2f}, Low={candles[-1][1]:.2f}, Close={candles[-1][2]:.2f}")
        
        # Расчет индикаторов
        print("\n📈 Расчет индикаторов...")
        
        ema200 = calculate_ema(prices, 200)
        
        # Для предыдущего значения EMA используем prices с отступом
        # но нужно убедиться, что данных достаточно
        if len(prices) > 200:
            # Берем цены без последней для расчета предыдущей EMA
            prices_prev = prices[:-1]
            ema200_prev = calculate_ema(prices_prev, 200)
        else:
            ema200_prev = None
            
        adx = calculate_adx(candles, 14)
        atr = calculate_atr(candles, 14)
        
        # Защита от None
        if adx is None:
            adx = 0
        if atr is None:
            atr = 0
        
        print(f"   EMA200 = {ema200:.2f}" if ema200 else "   EMA200 = None")
        print(f"   EMA200_prev = {ema200_prev:.2f}" if ema200_prev else "   EMA200_prev = None")
        print(f"   ADX = {adx:.2f}")
        print(f"   ATR = {atr:.4f}")
        
        last_price = prices[-1]
        print(f"\n💰 Текущая цена BTC: {last_price:.2f}")
        print(f"📊 ATR в % от цены: {(atr/last_price*100):.2f}%")
        
        # Определение режима
        print("\n🔍 ОПРЕДЕЛЕНИЕ РЕЖИМА:")
        
        if ema200 is not None and ema200_prev is not None:
            slope = (ema200 - ema200_prev) / ema200_prev
            print(f"📈 Наклон EMA200: {slope:.6f}")
            
            if slope > 0.0005 and adx > 20:
                regime = "TREND_UP"
                score = 1
                print(f"✅ TREND_UP: наклон={slope:.6f} > 0.0005, ADX={adx:.2f} > 20")
            elif slope < -0.0005 and adx > 20:
                regime = "TREND_DOWN"
                score = -1
                print(f"✅ TREND_DOWN: наклон={slope:.6f} < -0.0005, ADX={adx:.2f} > 20")
            elif atr > last_price * 0.02:
                regime = "VOLATILE"
                score = 0.2
                print(f"✅ VOLATILE: ATR={atr:.4f} > {last_price*0.02:.4f} (2% от цены)")
            elif adx > 25:
                regime = "VOLATILE"
                score = 0.2
                print(f"✅ VOLATILE: ADX={adx:.2f} > 25 (без тренда)")
            else:
                regime = "RANGE"
                score = 0
                print(f"➡️ RANGE: нет условий для тренда или волатильности")
        else:
            print("⚠️ Нет данных EMA200, используем только ADX")
            if adx > 25:
                regime = "VOLATILE"
                score = 0.2
                print(f"✅ Режим: VOLATILE (ADX={adx:.2f} > 25)")
            elif adx > 20:
                regime = "TREND_WEAK"
                score = 0.1
                print(f"⚠️ Режим: TREND_WEAK (ADX={adx:.2f} между 20 и 25)")
            else:
                regime = "RANGE"
                score = 0
                print(f"➡️ Режим: RANGE (ADX={adx:.2f} < 20)")
        
        result = {
            'regime': regime,
            'score': score,
            'atr': round(atr, 4),
            'adx': round(adx, 2),
            'price': round(last_price, 2),
            'slope': round(slope, 6) if 'slope' in locals() else 0
        }
        
        print("\n" + "="*70)
        print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        print(f"   Режим: {result['regime']}")
        print(f"   Скор: {result['score']}")
        print(f"   ADX: {result['adx']}")
        print(f"   ATR: {result['atr']}")
        print(f"   Цена BTC: ${result['price']}")
        print("="*70)
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

def regime_classifier(candles, prices, symbol="BTC-USDT"):
    """
    Классификатор рыночного режима для любой монеты
    """
    try:
        if not candles or len(candles) < 200 or not prices or len(prices) < 200:
            return {'regime': 'UNKNOWN', 'score': 0, 'atr': 0, 'slope': 0, 'adx': 0}
        
        formatted_candles = []
        for c in candles:
            if isinstance(c, dict):
                formatted_candles.append((float(c['high']), float(c['low']), float(c['close'])))
            elif isinstance(c, (list, tuple)) and len(c) >= 3:
                formatted_candles.append((float(c[0]), float(c[1]), float(c[2])))
            else:
                return {'regime': 'UNKNOWN', 'score': 0, 'atr': 0, 'slope': 0, 'adx': 0}
        
        ema200 = calculate_ema(prices, 200)
        
        # Для предыдущего EMA нужно достаточно данных
        if len(prices) > 200:
            ema200_prev = calculate_ema(prices[:-1], 200)
        else:
            ema200_prev = None
            
        adx = calculate_adx(formatted_candles, 14)
        atr = calculate_atr(formatted_candles, 14)
        
        if adx is None:
            adx = 0
        if atr is None:
            atr = 0
        
        if ema200 is None or ema200_prev is None:
            # Используем только ADX для классификации
            if adx > 25:
                return {'regime': 'VOLATILE', 'score': 0.2, 'atr': round(atr, 4), 'slope': 0, 'adx': round(adx, 2)}
            elif adx > 20:
                return {'regime': 'TREND_WEAK', 'score': 0.1, 'atr': round(atr, 4), 'slope': 0, 'adx': round(adx, 2)}
            else:
                return {'regime': 'RANGE', 'score': 0, 'atr': round(atr, 4), 'slope': 0, 'adx': round(adx, 2)}
        
        slope = (ema200 - ema200_prev) / ema200_prev if ema200_prev != 0 else 0
        last_price = prices[-1] if prices else 0
        
        if slope > 0.0005 and adx > 20:
            return {'regime': 'TREND_UP', 'score': 1, 'atr': round(atr, 4), 'slope': round(slope, 6), 'adx': round(adx, 2)}
        elif slope < -0.0005 and adx > 20:
            return {'regime': 'TREND_DOWN', 'score': -1, 'atr': round(atr, 4), 'slope': round(slope, 6), 'adx': round(adx, 2)}
        elif atr and atr > last_price * 0.02:
            return {'regime': 'VOLATILE', 'score': 0.2, 'atr': round(atr, 4), 'slope': round(slope, 6), 'adx': round(adx, 2)}
        elif adx > 25:
            return {'regime': 'VOLATILE', 'score': 0.2, 'atr': round(atr, 4), 'slope': round(slope, 6), 'adx': round(adx, 2)}
        else:
            return {'regime': 'RANGE', 'score': 0, 'atr': round(atr, 4), 'slope': round(slope, 6), 'adx': round(adx, 2)}
        
    except Exception:
        return {'regime': 'UNKNOWN', 'score': 0, 'atr': 0, 'slope': 0, 'adx': 0}

if __name__ == "__main__":
    # При прямом запуске анализируем BTC
    analyze_btc_regime()