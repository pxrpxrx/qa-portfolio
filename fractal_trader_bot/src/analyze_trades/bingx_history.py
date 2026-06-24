# bx_stats_from_db.py
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('StatsFromDB')

class BingXStatsFromDB:
    """
    Анализатор статистики на основе локальной БД positions.db
    Работает в тестовой сети VST, не требует API
    """
    
    def __init__(self, db_path: str = 'positions.db'):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise Exception(f"❌ БД не найдена: {db_path}")
        
        logger.info(f"📊 Анализ БД: {db_path}")
        logger.info("🌐 Режим: ТЕСТНЕТ (анализ локальной БД)")
    
    def get_all_trades(self) -> List[Dict]:
        """Получение всех закрытых сделок из БД"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(positions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Формируем запрос в зависимости от доступных колонок
        select_cols = """
            symbol, side, entry_price, quantity, 
            exit_price, realized_pnl, realized_pnl_percent, 
            exit_reason, entry_time, exit_time
        """
        
        # Добавляем stop_percent и take_percent если они есть
        if 'stop_percent' in columns:
            select_cols += ", stop_percent, take_percent"
        
        cursor.execute(f'''
            SELECT {select_cols}
            FROM positions 
            WHERE status = 'CLOSED'
            ORDER BY exit_time DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            try:
                trade = {
                    'symbol': row[0],
                    'side': row[1],
                    'entry_price': row[2],
                    'quantity': row[3],
                    'exit_price': row[4],
                    'pnl': row[5] if row[5] is not None else 0,
                    'pnl_percent': row[6] if row[6] is not None else 0,
                    'exit_reason': row[7],
                    'entry_time': row[8],
                    'exit_time': row[9],
                }
                
                # Добавляем проценты если они есть
                if len(row) > 10:
                    trade['stop_percent'] = row[10]
                    trade['take_percent'] = row[11]
                
                trades.append(trade)
            except Exception as e:
                logger.error(f"Ошибка парсинга сделки: {e}")
                continue
        
        logger.info(f"📥 Загружено закрытых сделок: {len(trades)}")
        return trades
    
    def filter_by_days(self, trades: List[Dict], days: int) -> List[Dict]:
        """Фильтрация сделок по количеству дней"""
        if days <= 0:
            return trades
        
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        
        for trade in trades:
            try:
                exit_time = datetime.fromisoformat(trade['exit_time'])
                if exit_time >= cutoff:
                    filtered.append(trade)
            except:
                continue
        
        return filtered
    
    def calculate_stats(self, trades: List[Dict]) -> Dict:
        """Расчет статистики по сделкам"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'max_win': 0.0,
                'max_loss': 0.0,
                'total_pnl_percent': 0.0,
                'avg_pnl_percent': 0.0,
                'by_symbol': {},
                'by_reason': {},
                'recent_trades': []
            }
        
        total_pnl = 0
        total_pnl_percent = 0
        winning = 0
        losing = 0
        max_win = 0
        max_loss = 0
        by_symbol = {}
        by_reason = {}
        
        for trade in trades:
            pnl = trade['pnl']
            pnl_percent = trade['pnl_percent']
            total_pnl += pnl
            total_pnl_percent += pnl_percent
            
            if pnl > 0:
                winning += 1
                max_win = max(max_win, pnl)
            elif pnl < 0:
                losing += 1
                max_loss = min(max_loss, pnl)
            
            # Статистика по монетам
            symbol = trade['symbol']
            if symbol not in by_symbol:
                by_symbol[symbol] = {
                    'trades': 0,
                    'pnl': 0,
                    'wins': 0,
                    'losses': 0,
                    'avg_pnl': 0
                }
            by_symbol[symbol]['trades'] += 1
            by_symbol[symbol]['pnl'] += pnl
            if pnl > 0:
                by_symbol[symbol]['wins'] += 1
            elif pnl < 0:
                by_symbol[symbol]['losses'] += 1
            
            # Статистика по причинам закрытия
            reason = trade['exit_reason'] or 'UNKNOWN'
            if reason not in by_reason:
                by_reason[reason] = {
                    'trades': 0,
                    'pnl': 0
                }
            by_reason[reason]['trades'] += 1
            by_reason[reason]['pnl'] += pnl
        
        total = len(trades)
        win_rate = (winning / total * 100) if total > 0 else 0
        
        # Рассчитываем средние по символам
        for symbol in by_symbol:
            by_symbol[symbol]['avg_pnl'] = round(
                by_symbol[symbol]['pnl'] / by_symbol[symbol]['trades'], 2
            )
            by_symbol[symbol]['win_rate'] = round(
                (by_symbol[symbol]['wins'] / by_symbol[symbol]['trades'] * 100), 1
            ) if by_symbol[symbol]['trades'] > 0 else 0
        
        # Последние 10 сделок
        recent_trades = trades[:10]
        
        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round(total_pnl_percent, 2),
            'avg_pnl': round(total_pnl / total, 2),
            'avg_pnl_percent': round(total_pnl_percent / total, 2) if total > 0 else 0,
            'max_win': round(max_win, 2),
            'max_loss': round(max_loss, 2),
            'by_symbol': by_symbol,
            'by_reason': by_reason,
            'recent_trades': recent_trades
        }
    
    def print_stats(self, days: int = 30):
        """Вывод статистики"""
        # Получаем все сделки
        all_trades = self.get_all_trades()
        
        # Фильтруем по дням
        trades = self.filter_by_days(all_trades, days)
        
        if not trades:
            print("\n" + "="*80)
            print(f"📊 СТАТИСТИКА ЗА {days} ДНЕЙ")
            print("="*80)
            print("❌ Нет закрытых сделок за указанный период")
            print("="*80)
            return
        
        stats = self.calculate_stats(trades)
        
        print("\n" + "="*90)
        print(f"📊 СТАТИСТИКА ТОРГОВЛИ (последние {days} дней)")
        print("="*90)
        
        # Основные показатели
        print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего сделок: {stats['total_trades']}")
        print(f"   ✅ Прибыльных: {stats['winning_trades']}")
        print(f"   ❌ Убыточных: {stats['losing_trades']}")
        print(f"   🎯 Win rate: {stats['win_rate']}%")
        
        print(f"\n💰 ФИНАНСОВЫЕ ПОКАЗАТЕЛИ:")
        print(f"   Общий P&L: {stats['total_pnl']:+.2f} USDT")
        print(f"   Общий P&L %: {stats['total_pnl_percent']:+.2f}%")
        print(f"   Средняя сделка: {stats['avg_pnl']:+.2f} USDT")
        print(f"   Средний %: {stats['avg_pnl_percent']:+.2f}%")
        print(f"   Макс. прибыль: {stats['max_win']:+.2f} USDT")
        print(f"   Макс. убыток: {stats['max_loss']:+.2f} USDT")
        
        # Статистика по монетам
        if stats['by_symbol']:
            print(f"\n🥇 СТАТИСТИКА ПО МОНЕТАМ:")
            sorted_symbols = sorted(
                stats['by_symbol'].items(), 
                key=lambda x: abs(x[1]['pnl']), 
                reverse=True
            )
            
            for symbol, data in sorted_symbols:
                arrow = "🟢" if data['pnl'] > 0 else "🔴"
                print(f"   {arrow} {symbol:<15} | "
                      f"Сделок: {data['trades']:3d} | "
                      f"P&L: {data['pnl']:+.2f} | "
                      f"Средняя: {data['avg_pnl']:+.2f} | "
                      f"Win%: {data['win_rate']}%")
        
        # Статистика по причинам закрытия
        if stats['by_reason']:
            print(f"\n🎯 ПРИЧИНЫ ЗАКРЫТИЯ:")
            for reason, data in stats['by_reason'].items():
                arrow = "🟢" if data['pnl'] > 0 else "🔴"
                print(f"   {reason:<12}: {data['trades']} сделок, P&L: {arrow}{data['pnl']:+.2f}")
        
        # Последние сделки
        if stats['recent_trades']:
            print(f"\n🕐 ПОСЛЕДНИЕ 10 СДЕЛОК:")
            print(f"   {'Символ':<12} {'Сторона':<6} {'Вход':>8} {'Выход':>8} {'P&L':>8} {'%':>6} {'Причина':<12}")
            print(f"   " + "-"*70)
            
            for t in stats['recent_trades']:
                arrow = "🟢" if t['pnl'] > 0 else "🔴"
                side_symbol = "LONG" if t['side'] == "BUY" or t['side'] == "LONG" else "SHORT"
                print(f"   {arrow} {t['symbol']:<12} "
                      f"{side_symbol:<6} "
                      f"{t['entry_price']:>8.4f} "
                      f"{t['exit_price']:>8.4f} "
                      f"{t['pnl']:>+8.2f} "
                      f"{t['pnl_percent']:>+6.1f}% "
                      f"{t['exit_reason'] or 'UNKNOWN':<12}")
        
        print("="*90)
    
    def export_to_csv(self, filename: str = 'trades_export.csv'):
        """Экспорт всех сделок в CSV"""
        import csv
        
        trades = self.get_all_trades()
        
        if not trades:
            print("❌ Нет сделок для экспорта")
            return
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Заголовки
            writer.writerow([
                'Символ', 'Сторона', 'Цена входа', 'Количество',
                'Цена выхода', 'P&L', 'P&L %', 'Причина', 'Время входа', 'Время выхода'
            ])
            
            # Данные
            for t in trades:
                writer.writerow([
                    t['symbol'],
                    'LONG' if t['side'] in ['BUY', 'LONG'] else 'SHORT',
                    f"{t['entry_price']:.4f}",
                    f"{t['quantity']:.4f}",
                    f"{t['exit_price']:.4f}",
                    f"{t['pnl']:+.2f}",
                    f"{t['pnl_percent']:+.1f}",
                    t['exit_reason'] or 'UNKNOWN',
                    t['entry_time'],
                    t['exit_time']
                ])
        
        print(f"✅ Экспортировано {len(trades)} сделок в {filename}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Статистика из positions.db')
    parser.add_argument('--days', type=int, default=30, help='Период в днях')
    parser.add_argument('--db', type=str, default='positions.db', help='Путь к БД')
    parser.add_argument('--export', type=str, help='Экспорт в CSV (укажите имя файла)')
    
    args = parser.parse_args()
    
    try:
        analyzer = BingXStatsFromDB(db_path=args.db)
        
        if args.export:
            analyzer.export_to_csv(args.export)
        else:
            analyzer.print_stats(days=args.days)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()