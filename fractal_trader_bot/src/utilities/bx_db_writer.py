# bx_db_writer.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import logging
from threading import Lock
import threading

logger = logging.getLogger('BxDBWriter')

class BingXDBWriter:
    """
    Модуль для записи данных о сделках в positions.db
    Создаёт БД если её нет, инициализирует структуру таблиц
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls, db_path: str = 'positions.db'):
        """Синглтон для предотвращения множественных подключений"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = 'positions.db'):
        """Инициализация подключения к БД"""
        if self._initialized:
            return
            
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._init_db()
        self._initialized = True
        logger.info(f"💾 Инициализирован DB Writer: {db_path}")
    
    def _get_connection(self):
        """Получение соединения с БД (thread-local)"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(str(self.db_path))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self):
        """Создание таблиц если их нет"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Таблица позиций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                entry_time TEXT NOT NULL,
                exit_price REAL,
                exit_time TEXT,
                realized_pnl REAL,
                realized_pnl_percent REAL,
                status TEXT DEFAULT 'OPEN',
                exit_reason TEXT,
                stop_percent REAL,
                take_percent REAL,
                max_pnl REAL,
                min_pnl REAL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для быстрого поиска
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_positions_symbol 
            ON positions(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_positions_status 
            ON positions(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_positions_exit_time 
            ON positions(exit_time)
        ''')
        
        # Таблица для статистики по монетам (кеш)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbol_stats (
                symbol TEXT PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                avg_pnl REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.debug("✅ Структура БД проверена/создана")
    
    def add_position(self, 
                    symbol: str,
                    side: str,
                    entry_price: float,
                    quantity: float,
                    stop_percent: float,
                    take_percent: float,
                    metadata: Optional[Dict] = None) -> int:
        """
        Добавление новой открытой позиции
        Возвращает ID созданной записи
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        entry_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO positions (
                symbol, side, entry_price, quantity, entry_time,
                stop_percent, take_percent, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol, side, entry_price, quantity, entry_time,
            stop_percent, take_percent, 'OPEN',
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        position_id = cursor.lastrowid
        logger.info(f"📝 Записана новая позиция #{position_id}: {symbol} {side}")
        
        return position_id
    
    def update_position(self, 
                       symbol: str,
                       exit_price: float,
                       realized_pnl: float,
                       realized_pnl_percent: float,
                       exit_reason: str,
                       metadata: Optional[Dict] = None):
        """
        Обновление закрытой позиции
        Ищет OPEN позицию по символу и закрывает её
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        exit_time = datetime.now().isoformat()
        
        # Находим открытую позицию
        cursor.execute('''
            SELECT id, entry_price, quantity 
            FROM positions 
            WHERE symbol = ? AND status = 'OPEN'
            ORDER BY entry_time DESC
            LIMIT 1
        ''', (symbol,))
        
        row = cursor.fetchone()
        if not row:
            logger.warning(f"⚠️ Не найдена открытая позиция для {symbol}")
            return None
        
        position_id = row[0]
        entry_price = row[1]
        
        # Обновляем позицию
        cursor.execute('''
            UPDATE positions 
            SET exit_price = ?,
                exit_time = ?,
                realized_pnl = ?,
                realized_pnl_percent = ?,
                status = 'CLOSED',
                exit_reason = ?,
                metadata = CASE 
                    WHEN metadata IS NULL THEN ?
                    ELSE json_patch(metadata, ?)
                END
            WHERE id = ?
        ''', (
            exit_price, exit_time, realized_pnl, realized_pnl_percent,
            exit_reason,
            json.dumps(metadata) if metadata else None,
            json.dumps(metadata) if metadata else None,
            position_id
        ))
        
        conn.commit()
        
        # Обновляем статистику по монете
        self._update_symbol_stats(symbol, realized_pnl)
        
        logger.info(f"📝 Закрыта позиция #{position_id}: {symbol} | "
                   f"P&L: {realized_pnl:+.4f} ({realized_pnl_percent:+.1f}%) | "
                   f"Причина: {exit_reason}")
        
        return position_id
    
    def _update_symbol_stats(self, symbol: str, pnl: float):
        """Обновление кешированной статистики по монете"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Получаем текущую статистику
        cursor.execute('''
            SELECT total_trades, winning_trades, losing_trades, total_pnl
            FROM symbol_stats
            WHERE symbol = ?
        ''', (symbol,))
        
        row = cursor.fetchone()
        
        if row:
            # Обновляем существующую
            total_trades = row[0] + 1
            winning_trades = row[1] + (1 if pnl > 0 else 0)
            losing_trades = row[2] + (1 if pnl < 0 else 0)
            total_pnl = row[3] + pnl
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            avg_pnl = total_pnl / total_trades
            
            cursor.execute('''
                UPDATE symbol_stats 
                SET total_trades = ?,
                    winning_trades = ?,
                    losing_trades = ?,
                    total_pnl = ?,
                    avg_pnl = ?,
                    win_rate = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            ''', (total_trades, winning_trades, losing_trades, 
                  total_pnl, avg_pnl, win_rate, symbol))
        else:
            # Создаём новую запись
            winning_trades = 1 if pnl > 0 else 0
            losing_trades = 1 if pnl < 0 else 0
            win_rate = 100 if pnl > 0 else 0
            
            cursor.execute('''
                INSERT INTO symbol_stats 
                (symbol, total_trades, winning_trades, losing_trades, 
                 total_pnl, avg_pnl, win_rate)
                VALUES (?, 1, ?, ?, ?, ?, ?)
            ''', (symbol, winning_trades, losing_trades, pnl, pnl, win_rate))
        
        conn.commit()
    
    def get_open_positions(self) -> list:
        """Получение всех открытых позиций"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, symbol, side, entry_price, quantity, entry_time,
                   stop_percent, take_percent
            FROM positions 
            WHERE status = 'OPEN'
            ORDER BY entry_time DESC
        ''')
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Получение открытой позиции по символу"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, symbol, side, entry_price, quantity, entry_time,
                   stop_percent, take_percent
            FROM positions 
            WHERE symbol = ? AND status = 'OPEN'
            ORDER BY entry_time DESC
            LIMIT 1
        ''', (symbol,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_recent_trades(self, limit: int = 10) -> list:
        """Получение последних закрытых сделок"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, side, entry_price, exit_price, 
                   realized_pnl, realized_pnl_percent, exit_reason,
                   entry_time, exit_time
            FROM positions 
            WHERE status = 'CLOSED'
            ORDER BY exit_time DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def cleanup_old_positions(self, days: int = 30):
        """Очистка старых записей (опционально)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            DELETE FROM positions 
            WHERE status = 'CLOSED' AND exit_time < ?
        ''', (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        
        if deleted > 0:
            logger.info(f"🧹 Удалено старых записей: {deleted}")
        
        return deleted
    
    def close(self):
        """Закрытие соединения с БД"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')
            logger.debug("🔒 Соединение с БД закрыто")


# Контекстный менеджер для автоматического закрытия
class DBWriterContext:
    def __init__(self, db_path: str = 'positions.db'):
        self.writer = BingXDBWriter(db_path)
    
    def __enter__(self):
        return self.writer
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.writer.close()


# Функция для легкого импорта в оркестратор
def get_db_writer(db_path: str = 'positions.db') -> BingXDBWriter:
    """Получение экземпляра DB Writer (синглтон)"""
    return BingXDBWriter(db_path)


# Тестовый запуск
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Тестирование
    print("="*60)
    print("ТЕСТИРОВАНИЕ DB WRITER")
    print("="*60)
    
    # Создаем экземпляр
    db = BingXDBWriter("test_positions.db")
    
    # Добавляем тестовую позицию
    pos_id = db.add_position(
        symbol="BTC-USDT",
        side="BUY",
        entry_price=50000.0,
        quantity=0.001,
        stop_percent=0.25,
        take_percent=0.9,
        metadata={"strategy": "scalp", "atr": 0.5}
    )
    print(f"✅ Добавлена позиция #{pos_id}")
    
    # Закрываем позицию
    db.update_position(
        symbol="BTC-USDT",
        exit_price=50450.0,
        realized_pnl=0.45,
        realized_pnl_percent=0.9,
        exit_reason="TAKE_PROFIT",
        metadata={"slippage": 0.01}
    )
    
    # Проверяем открытые позиции
    open_positions = db.get_open_positions()
    print(f"📊 Открытых позиций: {len(open_positions)}")
    
    # Проверяем последние сделки
    recent = db.get_recent_trades()
    print(f"🕐 Последних сделок: {len(recent)}")
    
    db.close()
    print("="*60)