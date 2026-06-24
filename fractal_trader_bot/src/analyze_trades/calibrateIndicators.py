# calibrate_indicators.py
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

conn = sqlite3.connect('trades_new.db')

# Загружаем все сделки с ВСЕМИ полями
df = pd.read_sql_query("""
    SELECT 
        id, symbol, direction, entry_price, exit_price,
        position_size, stop_loss, take_profit,  -- ДОБАВИЛ stop_loss и take_profit
        pnl, pnl_percent, exit_reason,
        final_score, atr_entry,
        datetime(entry_time) as entry_time,
        datetime(exit_time) as exit_time
    FROM trades_new
    WHERE status = 'CLOSED'
    ORDER BY entry_time
""", conn)

print(f"\n{'='*70}")
print(f"КАЛИБРОВКА ИНДИКАТОРОВ")
print(f"{'='*70}")
print(f"Всего сделок: {len(df)}")
print(f"Прибыльных: {len(df[df['pnl']>0])} ({len(df[df['pnl']>0])/len(df)*100:.2f}%)")
print(f"Убыточных: {len(df[df['pnl']<0])}")

# === 1. АНАЛИЗ ТРЕНДОВОЙ СИСТЕМЫ ===
print(f"\n{'='*70}")
print(f"1. АНАЛИЗ ТРЕНДОВОЙ СИСТЕМЫ")
print(f"{'='*70}")

# Смотрим сделки по направлениям
trend_analysis = df.groupby('direction').agg({
    'pnl': ['count', 'mean', 'sum'],
    'pnl_percent': 'mean',
    'exit_reason': lambda x: (x == 'take_profit').sum()
}).round(2)

trend_analysis.columns = ['сделок', 'средний P&L', 'сумма P&L', 'средний %', 'тейков']
print(trend_analysis)

# === 2. АНАЛИЗ МОМЕНТУМ СИСТЕМЫ ===
print(f"\n{'='*70}")
print(f"2. АНАЛИЗ МОМЕНТУМ СИСТЕМЫ")
print(f"{'='*70}")

# Разбиваем сигналы по квартилям
# Проверяем уникальность значений
unique_scores = df['final_score'].nunique()
if unique_scores < 4:
    print(f"⚠️ Мало уникальных значений скора ({unique_scores}), использую ручные границы")
    momentum_bins = pd.cut(df['final_score'], 
                           bins=[-float('inf'), 0.3, 0.5, 0.7, float('inf')],
                           labels=['Очень слабый', 'Слабый', 'Средний', 'Сильный'])
else:
    momentum_bins = pd.qcut(df['final_score'], q=4, 
                            labels=['Q1(слабый)', 'Q2', 'Q3', 'Q4(сильный)'], 
                            duplicates='drop')
momentum_analysis = df.groupby(momentum_bins).agg({
    'pnl': ['count', 'mean', 'sum'],
    'exit_reason': lambda x: (x == 'take_profit').sum()
}).round(2)

momentum_analysis.columns = ['сделок', 'средний P&L', 'сумма P&L', 'тейков']
print(momentum_analysis)

# === 3. АНАЛИЗ ФРАКТАЛЬНОЙ СИСТЕМЫ ===
print(f"\n{'='*70}")
print(f"3. АНАЛИЗ ФРАКТАЛЬНОЙ СИСТЕМЫ")
print(f"{'='*70}")

# Тут нужны данные по фракталам, если их нет в БД - пропускаем
if 'fractal_score' in df.columns:
    fractal_analysis = df.groupby(pd.cut(df['fractal_score'], bins=[0,0.3,0.7,1])).agg({
        'pnl': ['count', 'mean', 'sum']
    }).round(2)
    print(fractal_analysis)
else:
    print("Нет данных по фракталам в БД")

# === 4. АНАЛИЗ ATR И СТОПОВ ===
print(f"\n{'='*70}")
print(f"4. АНАЛИЗ ATR И СТОПОВ")
print(f"{'='*70}")

# Рассчитываем расстояние до стопа в ATR
df['stop_distance'] = abs(df['entry_price'] - df['stop_loss']) / df['atr_entry']
df['take_distance'] = abs(df['entry_price'] - df['take_profit']) / df['atr_entry']

print(f"Среднее расстояние до стопа: {df['stop_distance'].mean():.2f} ATR")
print(f"Среднее расстояние до тейка: {df['take_distance'].mean():.2f} ATR")
print(f"Соотношение риск/прибыль: {df['take_distance'].mean() / df['stop_distance'].mean():.2f}")

# Анализ оптимального стопа
stop_analysis = []
for mult in np.arange(0.5, 3.0, 0.25):
    would_survive = df[df['stop_distance'] > mult].shape[0]
    stop_analysis.append({
        'стоп_ATR': mult,
        'выжило_сделок': would_survive,
        '%': would_survive/len(df)*100
    })
print("\nАнализ разных уровней стопа:")
print(pd.DataFrame(stop_analysis).head(10))

# === 5. АНАЛИЗ ВРЕМЕНИ СДЕЛОК ===
print(f"\n{'='*70}")
print(f"5. АНАЛИЗ ВРЕМЕНИ СДЕЛОК")
print(f"{'='*70}")

df['duration'] = (pd.to_datetime(df['exit_time']) - pd.to_datetime(df['entry_time'])).dt.total_seconds() / 60
print(f"Средняя длительность: {df['duration'].mean():.1f} мин")
print(f"Медианная длительность: {df['duration'].median():.1f} мин")

win = df[df['pnl']>0]
loss = df[df['pnl']<0]
print(f"Длительность прибыльных: {win['duration'].mean():.1f} мин")
print(f"Длительность убыточных: {loss['duration'].mean():.1f} мин")

# === 6. ОПТИМАЛЬНЫЙ ПОРОГ СИГНАЛА ===
print(f"\n{'='*70}")
print(f"6. ОПТИМАЛЬНЫЙ ПОРОГ СИГНАЛА")
print(f"{'='*70}")

thresholds = np.arange(0.3, 0.9, 0.05)
for th in thresholds:
    filtered = df[df['final_score'] >= th]
    if len(filtered) > 5:  # Минимум 5 сделок
        win_rate = len(filtered[filtered['pnl']>0]) / len(filtered) * 100
        total_pnl = filtered['pnl'].sum()
        print(f"Порог {th:.2f}: сделок={len(filtered)}, win_rate={win_rate:.1f}%, P&L={total_pnl:+.2f}")

# === 7. КОРРЕЛЯЦИЯ СИГНАЛОВ С РЕЗУЛЬТАТОМ ===
print(f"\n{'='*70}")
print(f"7. КОРРЕЛЯЦИЯ СИГНАЛОВ")
print(f"{'='*70}")

df['profitable'] = (df['pnl'] > 0).astype(int)
correlation = df['final_score'].corr(df['profitable'])
print(f"Корреляция сигнала с прибыльностью: {correlation:.3f}")

if correlation < 0:
    print("⚠️ Сигнал работает В ОБРАТНУЮ сторону! Нужно инвертировать.")
elif correlation < 0.1:
    print("⚠️ Сигнал почти не влияет на результат.")
else:
    print("✅ Сигнал положительно влияет.")

# === 8. ИНВЕРСИЯ СИГНАЛОВ (если нужно) ===
print(f"\n{'='*70}")
print(f"8. ТЕСТ ИНВЕРСИИ СИГНАЛОВ")
print(f"{'='*70}")

df['inverse_trade'] = df['pnl'] * -1  # Если бы торговали в противоположную сторону
print(f"Текущий P&L: {df['pnl'].sum():.2f}")
print(f"Инверсный P&L: {df['inverse_trade'].sum():.2f}")
print(f"Улучшение: {(df['inverse_trade'].sum() - df['pnl'].sum()):.2f}")

if df['inverse_trade'].sum() > df['pnl'].sum():
    print("⚠️ НУЖНО ТОРГОВАТЬ В ПРОТИВОПОЛОЖНУЮ СТОРОНУ!")

# === 9. МОНЕТЫ-УБИЙЦЫ ===
print(f"\n{'='*70}")
print(f"9. ХУДШИЕ МОНЕТЫ")
print(f"{'='*70}")

bad_coins = df.groupby('symbol').agg({
    'pnl': ['count', 'sum', 'mean'],
    'exit_reason': lambda x: (x == 'stop_loss').sum()
}).round(2)
bad_coins.columns = ['сделок', 'сумма P&L', 'средний P&L', 'стопов']
bad_coins = bad_coins.sort_values(('сумма P&L')).head(10)
print(bad_coins)

print(f"\n{'='*70}")
print(f"10. ЛУЧШИЕ МОНЕТЫ")
print(f"{'='*70}")
good_coins = df.groupby('symbol').agg({
    'pnl': ['count', 'sum', 'mean'],
    'exit_reason': lambda x: (x == 'take_profit').sum()
}).round(2)
good_coins.columns = ['сделок', 'сумма P&L', 'средний P&L', 'тейков']
good_coins = good_coins.sort_values(('сумма P&L'), ascending=False).head(10)
print(good_coins)

conn.close()