import pytest
import sqlite3
import os
from datetime import datetime

# Временная БД для тестов
TEST_DB = 'test_exchange_bot.db'

@pytest.fixture
def db_connection():
    """Фикстура: создаёт временную БД для каждого теста"""
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    
    # Создаём таблицы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            state TEXT DEFAULT 'main',
            first_name TEXT,
            username TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            order_number TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    ''')
    
    conn.commit()
    yield conn
    conn.close()
    os.remove(TEST_DB)

def create_test_user(conn, chat_id, first_name="Test", username="test_user"):
    """Вспомогательная функция для создания тестового пользователя"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (chat_id, first_name, username)
        VALUES (?, ?, ?)
    ''', (chat_id, first_name, username))
    conn.commit()
    return cursor.lastrowid

def create_test_order(conn, chat_id, order_number="TEST001"):
    """Вспомогательная функция для создания тестовой заявки"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (chat_id, order_number, status, created_at)
        VALUES (?, ?, ?, ?)
    ''', (chat_id, order_number, 'pending', datetime.now().isoformat()))
    conn.commit()
    return cursor.lastrowid

# ===================================================
# ТЕСТЫ
# ===================================================

class TestDatabase:
    """Тесты для базы данных"""
    
    def test_create_user(self, db_connection):
        """Тест 1: Создание пользователя"""
        chat_id = 123456789
        create_test_user(db_connection, chat_id, "Иван", "ivan_test")
        
        cursor = db_connection.cursor()
        cursor.execute('SELECT first_name, username FROM users WHERE chat_id = ?', (chat_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "Иван"
        assert result[1] == "ivan_test"
    
    def test_create_order(self, db_connection):
        """Тест 2: Создание заявки"""
        chat_id = 123456789
        create_test_user(db_connection, chat_id)
        
        order_id = create_test_order(db_connection, chat_id, "ORD250621000001")
        
        cursor = db_connection.cursor()
        cursor.execute('SELECT order_number, status FROM orders WHERE order_id = ?', (order_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "ORD250621000001"
        assert result[1] == "pending"
    
    def test_update_order_status(self, db_connection):
        """Тест 3: Обновление статуса заявки"""
        chat_id = 123456789
        create_test_user(db_connection, chat_id)
        order_id = create_test_order(db_connection, chat_id)
        
        # Обновляем статус
        cursor = db_connection.cursor()
        cursor.execute('UPDATE orders SET status = ? WHERE order_id = ?', ('completed', order_id))
        db_connection.commit()
        
        # Проверяем
        cursor.execute('SELECT status FROM orders WHERE order_id = ?', (order_id,))
        result = cursor.fetchone()
        
        assert result[0] == "completed"
    
    def test_get_user_by_chat_id(self, db_connection):
        """Тест 4: Поиск пользователя по chat_id"""
        chat_id = 123456789
        create_test_user(db_connection, chat_id, "Петр", "petr_test")
        
        cursor = db_connection.cursor()
        cursor.execute('SELECT first_name, username FROM users WHERE chat_id = ?', (chat_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "Петр"
    
    def test_get_orders_by_user(self, db_connection):
        """Тест 5: Получение всех заявок пользователя"""
        chat_id = 123456789
        create_test_user(db_connection, chat_id)
        
        # Создаём 3 заявки
        for i in range(3):
            create_test_order(db_connection, chat_id, f"ORD{i:06d}")
        
        cursor = db_connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM orders WHERE chat_id = ?', (chat_id,))
        count = cursor.fetchone()[0]
        
        assert count == 3