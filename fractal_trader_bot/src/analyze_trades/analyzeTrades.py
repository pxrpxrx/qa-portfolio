# analyze_trades.py
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect('trades_new.db')

# Анализ по направлениям
df = pd.read_sql_query("""
    SELECT 
        direction,
        COUNT(*) as trades,
        AVG(pnl) as avg_pnl,
        SUM(pnl) as total_pnl,
        AVG(pnl_percent) as avg_return,
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
    FROM trades_new
    WHERE status = 'CLOSED'
    GROUP BY direction
""", conn)
print("\n📊 АНАЛИЗ ПО НАПРАВЛЕНИЯМ:")
print(df)

# Анализ по exit_reason
df2 = pd.read_sql_query("""
    SELECT 
        exit_reason,
        COUNT(*) as trades,
        AVG(pnl) as avg_pnl,
        SUM(pnl) as total_pnl
    FROM trades_new
    WHERE status = 'CLOSED'
    GROUP BY exit_reason
""", conn)
print("\n📊 АНАЛИЗ ПО ПРИЧИНАМ ВЫХОДА:")
print(df2)

# Анализ по сигналам
df3 = pd.read_sql_query("""
    SELECT 
        CASE 
            WHEN final_score >= 0.8 THEN 'HIGH'
            WHEN final_score >= 0.6 THEN 'MEDIUM'
            ELSE 'LOW'
        END as signal_level,
        COUNT(*) as trades,
        AVG(pnl) as avg_pnl,
        SUM(pnl) as total_pnl,
        AVG(pnl_percent) as avg_return
    FROM trades_new
    WHERE status = 'CLOSED'
    GROUP BY signal_level
    ORDER BY signal_level DESC
""", conn)
print("\n📊 АНАЛИЗ ПО СИЛЕ СИГНАЛА:")
print(df3)

conn.close()