# bx_atr.py 
import requests
from typing import Optional, Dict, List

class ATR:
    def __init__(self):
        self.url = "https://open-api-vst.bingx.com/openApi/swap/v3/quote/klines"
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Получение текущей цены"""
        try:
            url = "https://open-api-vst.bingx.com/openApi/swap/v2/quote/ticker"
            response = requests.get(url, params={'symbol': symbol}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    ticker = data.get('data')
                    if ticker:
                        return float(ticker.get('lastPrice', 0))
        except Exception as e:
            print(f"Ошибка: {e}")
        return None
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> Optional[List[Dict]]:
        """Получение свечей"""
        try:
            response = requests.get(
                self.url,
                params={'symbol': symbol, 'interval': interval, 'limit': limit},
                timeout=10
            )
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
            print(f"Ошибка: {e}")
        return None
    
    def calculate(self, symbol: str, timeframe: str, period: int = 14) -> Optional[Dict]:
        """Расчет ATR"""
        klines = self.get_klines(symbol, timeframe, period + 50)
        if not klines or len(klines) < period + 1:
            return None
        
        tr_values = []
        for i in range(1, len(klines)):
            tr = max(
                klines[i]['high'] - klines[i]['low'],
                abs(klines[i]['high'] - klines[i-1]['close']),
                abs(klines[i]['low'] - klines[i-1]['close'])
            )
            tr_values.append(tr)
        
        if len(tr_values) >= period:
            atr = sum(tr_values[:period]) / period
            for tr in tr_values[period:]:
                atr = (atr * (period - 1) + tr) / period
            
            return {
                'atr': round(atr, 8),
                'atr_3': round(atr * 3, 8),
                'atr_percent': round((atr / klines[-1]['close']) * 100, 4)
            }
        return None


# ============================================
# НАСТРОЙКИ
# ============================================

SYMBOL = "SUI-USDT"
TIMEFRAMES = ["15m", "1h", "1d"]
PERIOD = 14
CAPITAL = 1000  # Твой капитал в USDT
RISK_PERCENT = 1  # Риск 1% от капитала

# ============================================
# ПРАВИЛЬНЫЙ РАСЧЕТ ПОЗИЦИИ
# ============================================

def calculate_position(capital: float, risk_percent: float, stop_percent: float, entry_price: float) -> Dict:
    """
    ПРАВИЛЬНЫЙ расчет размера позиции
    
    stop_percent - это процент, на который упадет цена до стопа (в %)
    Пример: стоп 14.6% означает, что цена упадет на 14.6%
    
    Формула: 
    Риск (в USDT) = Позиция (в USDT) × (Стоп% / 100)
    Позиция = Риск / (Стоп% / 100)
    """
    risk_amount = capital * (risk_percent / 100)  # 10 USDT
    stop_percent_decimal = stop_percent / 100  # 0.146 для 14.6%
    
    # Размер позиции = Риск ÷ Процент стопа
    position_size = risk_amount / stop_percent_decimal
    quantity = position_size / entry_price
    
    return {
        'risk_usdt': round(risk_amount, 2),
        'stop_percent': stop_percent,
        'position_usdt': round(position_size, 2),
        'quantity': round(quantity, 8),
        'loss_at_stop': round(position_size * stop_percent_decimal, 2)  # Должно равняться risk_amount
    }


# ============================================
# ВЫВОД
# ============================================

if __name__ == "__main__":
    atr_calc = ATR()
    
    # Получаем текущую цену
    current_price = atr_calc.get_current_price(SYMBOL)
    
    if not current_price:
        print("❌ Не удалось получить цену")
        exit()
    
    print("="*60)
    print(f"📊 {SYMBOL}")
    print(f"💰 Капитал: {CAPITAL} USDT | Риск: {RISK_PERCENT}%")
    print(f"💵 Цена сейчас: ${current_price:.2f}")
    print("="*60)
    print("\n💡 ПОЯСНЕНИЕ:")
    print("   Размер позиции = Риск (10$) ÷ (Стоп% / 100)")
    print("   Пример: при стопе 14.6% → позиция = 10 ÷ 0.146 = 68.5$\n")
    
    for tf in TIMEFRAMES:
        result = atr_calc.calculate(SYMBOL, tf, PERIOD)
        
        if result:
            atr_3 = result['atr_3']
            stop_percent = (atr_3 / current_price) * 100  # Процент до стопа
            stop_price = current_price - atr_3
            
            # Правильный расчет позиции
            position = calculate_position(CAPITAL, RISK_PERCENT, stop_percent, current_price)
            
            print(f"\n{'='*60}")
            print(f"🕐 {tf.upper()}")
            print(f"{'='*60}")
            print(f"   ATR = ${result['atr']:.2f} ({result['atr_percent']}%)")
            print(f"   3 ATR = ${atr_3:.2f} ({stop_percent:.2f}%)")
            print(f"   Стоп-лосс = ${stop_price:.2f}")
            
            print(f"\n   📐 РАЗМЕР ПОЗИЦИИ (риск {RISK_PERCENT}%):")
            print(f"      Сумма: ${position['position_usdt']}")
            print(f"      Кол-во: {position['quantity']} {SYMBOL.replace('-USDT', '')}")
            print(f"      Потеря при стопе: ${position['loss_at_stop']} (должно быть {position['risk_usdt']}$)")
            
            # Дополнительная информация
            if position['position_usdt'] < 5:
                print(f"      ⚠️ Позиция очень маленькая (<5$) - не торгуй на этом ТФ")
            elif position['position_usdt'] > CAPITAL:
                print(f"      ⚠️ Нужно плечо {position['position_usdt']/CAPITAL:.1f}x")
            
        else:
            print(f"\n❌ {tf}: ошибка")
    
    print("\n" + "="*60)
    print("✅ ИСПРАВЛЕННАЯ ЛОГИКА:")
    print(f"   1% риск = Стоп% × Позиция")
    print(f"   Чем ШИРЕ стоп → тем БОЛЬШЕ позиция (нужно плечо)")
    print("="*60)