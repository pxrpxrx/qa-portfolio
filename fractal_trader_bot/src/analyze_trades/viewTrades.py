import sqlite3
import pandas as pd
from tabulate import tabulate

# Подключаемся к БД
conn = sqlite3.connect('trades.db')

# Смотрим открытые сделки
print("\n📊 ОТКРЫТЫЕ СДЕЛКИ")
df_open = pd.read_sql_query("SELECT * FROM trades WHERE status = 'OPEN'", conn)
if len(df_open) > 0:
    print(tabulate(df_open, headers='keys', tablefmt='grid', showindex=False))
else:
    print("Нет открытых сделок")

# Смотрим все сделки
print("\n📊 ВСЕ СДЕЛКИ")
df_all = pd.read_sql_query("SELECT * FROM trades ORDER BY entry_time DESC", conn)
if len(df_all) > 0:
    print(tabulate(df_all, headers='keys', tablefmt='grid', showindex=False))
    print(f"\n✅ Всего записей: {len(df_all)}")
else:
    print("Нет записей")

conn.close()