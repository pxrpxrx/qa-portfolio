import requests
import sqlite3
import json
import os
import asyncio
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from bestchange_api import BestChange

# ===================================================
# КОНФИГУРАЦИЯ
# ===================================================

ADMIN_IDS = [your_id]  

OPERATOR_CHANNEL_ID = {your_id}

# ===================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ===================================================

def init_db():
    """Создаёт таблицы для хранения состояний и заявок"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            state TEXT DEFAULT 'main',
            buy_currency TEXT,
            sell_currency TEXT,
            current_order_id INTEGER,
            client_card_number TEXT,
            client_phone_number TEXT,
            client_bank_name TEXT,
            client_full_name TEXT,
            first_name TEXT,
            username TEXT
        )
    ''')
    
    # Таблица для отложенных сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages_to_send (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            text TEXT,
            reply_markup TEXT,
            created_at TEXT,
            sent INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица заявок с РАЗДЕЛЬНЫМИ полями для реквизитов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            order_number TEXT,
            buy_currency TEXT,
            sell_currency TEXT,
            amount_rub REAL,
            amount_btc REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            paid_at TEXT,
            tx_hash TEXT,
            receipt_file_id TEXT,
            -- Реквизиты КЛИЕНТА (отправителя)
            client_card_number TEXT,
            client_phone_number TEXT,
            client_bank_name TEXT,
            client_full_name TEXT,
            -- Реквизиты ОПЕРАТОРА (получателя)
            operator_card_number TEXT,
            operator_bank_name TEXT,
            operator_full_name TEXT,
            operator_rub_amount REAL,
            -- Крипто-реквизиты оператора
            operator_wallet_address TEXT,
            operator_network TEXT,
            operator_crypto_amount REAL,
            payment_detail_id INTEGER
        )
    ''')
    
    # Таблица настроек админа
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    cursor.execute('INSERT OR IGNORE INTO admin_settings (key, value) VALUES ("bot_working", "True")')
    cursor.execute('INSERT OR IGNORE INTO admin_settings (key, value) VALUES ("usd_rub_rate", "0")')
    cursor.execute('INSERT OR IGNORE INTO admin_settings (key, value) VALUES ("btc_usd_rate", "0")')
    
    # Таблица реквизитов обменника
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT,
            name TEXT,
            network TEXT,
            address TEXT,
            details TEXT,
            min_amount REAL,
            max_amount REAL,
            total_limit REAL,
            used_amount REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user_state(chat_id):
    """Получает состояние пользователя"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT state, buy_currency, sell_currency, current_order_id FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {'state': result[0], 'buy_currency': result[1], 'sell_currency': result[2], 'current_order_id': result[3]}
    return {'state': 'main', 'buy_currency': None, 'sell_currency': None, 'current_order_id': None}

def update_user_state(chat_id, state=None, buy_currency=None, sell_currency=None, current_order_id=None):
    """Обновляет состояние пользователя"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT state FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    
    if not result:
        cursor.execute('INSERT INTO users (chat_id, state, buy_currency, sell_currency, current_order_id) VALUES (?, ?, ?, ?, ?)',
                      (chat_id, state or 'main', buy_currency, sell_currency, current_order_id))
    else:
        updates = []
        params = []
        if state is not None:
            updates.append('state = ?')
            params.append(state)
        if buy_currency is not None:
            updates.append('buy_currency = ?')
            params.append(buy_currency)
        if sell_currency is not None:
            updates.append('sell_currency = ?')
            params.append(sell_currency)
        if current_order_id is not None:
            updates.append('current_order_id = ?')
            params.append(current_order_id)
        
        if updates:
            params.append(chat_id)
            cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE chat_id = ?', params)
    
    conn.commit()
    conn.close()

def create_order(chat_id, buy_currency, sell_currency, amount):
    """Создаёт новую заявку с единым форматом номера"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    
    # Получаем следующий order_id для генерации номера
    cursor.execute('SELECT MAX(order_id) FROM orders')
    max_id = cursor.fetchone()[0]
    next_id = (max_id or 0) + 1
    
    # Единый формат: ORD + дата(6 цифр) + номер(6 цифр)
    # Пример: ORD240515000001
    date_str = datetime.now().strftime('%y%m%d')
    order_number = f"ORD{date_str}{next_id:06d}"
    
    cursor.execute('''
        INSERT INTO orders (chat_id, order_number, buy_currency, sell_currency, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, order_number, buy_currency, sell_currency, amount, datetime.now().isoformat()))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return order_id, order_number

def update_order_status(order_id, status=None, paid_at=None, tx_hash=None, receipt_file_id=None):
    """Обновляет статус заявки"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    
    updates = []
    params = []
    if status is not None:
        updates.append('status = ?')
        params.append(status)
    if paid_at is not None:
        updates.append('paid_at = ?')
        params.append(paid_at)
    if tx_hash is not None:
        updates.append('tx_hash = ?')
        params.append(tx_hash)
    if receipt_file_id is not None:
        updates.append('receipt_file_id = ?')
        params.append(receipt_file_id)
    
    if updates:
        params.append(order_id)
        cursor.execute(f'UPDATE orders SET {", ".join(updates)} WHERE order_id = ?', params)
        conn.commit()
    
    conn.close()

def get_admin_setting(key):
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM admin_settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_admin_setting(key, value):
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO admin_settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

def is_bot_working():
    return get_admin_setting('bot_working') == 'True'

def get_payment_details(currency=None, active_only=True):
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    if currency:
        cursor.execute('SELECT id, name, network, address, details, min_amount, max_amount, total_limit, used_amount FROM payment_details WHERE currency = ? AND is_active = 1', (currency,))
    else:
        cursor.execute('SELECT id, name, network, address, details, min_amount, max_amount, total_limit, used_amount, currency FROM payment_details WHERE is_active = 1')
    results = cursor.fetchall()
    conn.close()
    return results

def add_payment_detail(currency, name, network, address, details, min_amount, max_amount, total_limit):
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_details (currency, name, network, address, details, min_amount, max_amount, total_limit, used_amount) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (currency, name, network, address, details, min_amount, max_amount, total_limit, 0))
    conn.commit()
    conn.close()

def delete_payment_detail(detail_id):
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM payment_details WHERE id = ?', (detail_id,))
    conn.commit()
    conn.close()

def get_active_orders():
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT order_id, order_number, chat_id, amount, sell_currency, buy_currency, status, first_name, username FROM orders WHERE status IN ("pending_verification", "awaiting_confirmation") ORDER BY created_at DESC')
    results = cursor.fetchall()
    conn.close()
    return results

def check_payment_limit(payment_id, amount):
    """Проверяет, есть ли свободное место в лимите реквизита"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT total_limit, used_amount FROM payment_details WHERE id = ?', (payment_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        total_limit, used_amount = result
        available = total_limit - used_amount
        return available >= amount, available
    return False, 0

def update_payment_used(payment_id, amount):
    """Обновляет использованную сумму реквизита после успешного обмена"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE payment_details SET used_amount = used_amount + ? WHERE id = ?', (amount, payment_id))
    conn.commit()
    conn.close()

# ===================================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ КУРСОВ
# ===================================================

def get_btc_usdt():
    url = "https://api.bybit.com/v5/market/tickers"
    params = {'category': 'linear', 'symbol': 'BTCUSDT'}
    try:
        response = requests.get(url, params=params, timeout=25)
        data = response.json()
        if data['retCode'] == 0:
            return float(data['result']['list'][0]['lastPrice'])
        return None
    except Exception as e:
        print(f"Ошибка BTC/USDT: {e}")
        return None

def get_usd_rub():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(url, timeout=25)
        data = response.json()
        return float(data['Valute']['USD']['Value'])
    except Exception as e:
        print(f"Ошибка USD/RUB: {e}")
        return None

def get_rate(currency_from, currency_to):
    admin_usd_rub = float(get_admin_setting('usd_rub_rate') or 0)
    admin_btc_usd = float(get_admin_setting('btc_usd_rate') or 0)
    
    if currency_from == 'BTC' and currency_to == 'USDT':
        return admin_btc_usd if admin_btc_usd > 0 else get_btc_usdt()
    if currency_from == 'USDT' and currency_to == 'BTC':
        rate = admin_btc_usd if admin_btc_usd > 0 else get_btc_usdt()
        return 1 / rate if rate else None
    if currency_from == 'BTC' and currency_to == 'RUB':
        btc_usdt = admin_btc_usd if admin_btc_usd > 0 else get_btc_usdt()
        usd_rub = admin_usd_rub if admin_usd_rub > 0 else get_usd_rub()
        return btc_usdt * usd_rub if btc_usdt and usd_rub else None
    if currency_from == 'USDT' and currency_to == 'RUB':
        return admin_usd_rub if admin_usd_rub > 0 else get_usd_rub()
    if currency_from == 'RUB' and currency_to == 'USDT':
        usd_rub = admin_usd_rub if admin_usd_rub > 0 else get_usd_rub()
        return 1 / usd_rub if usd_rub else None
    return None

def get_all_rates():
    admin_usd_rub = float(get_admin_setting('usd_rub_rate') or 0)
    admin_btc_usd = float(get_admin_setting('btc_usd_rate') or 0)
    
    btc_usdt = admin_btc_usd if admin_btc_usd > 0 else get_btc_usdt()
    usd_rub = admin_usd_rub if admin_usd_rub > 0 else get_usd_rub()
    btc_rub = btc_usdt * usd_rub if btc_usdt and usd_rub else None
    
    return {
        'btc_usdt': btc_usdt,
        'usd_rub': usd_rub,
        'btc_rub': btc_rub,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ===================================================
# КЛАВИАТУРЫ
# ===================================================

def get_buy_keyboard():
    keyboard = [
        [InlineKeyboardButton("Купить BTC", callback_data="buy_BTC")],
        [InlineKeyboardButton("Купить USDT", callback_data="buy_USDT")],
        [InlineKeyboardButton("Купить RUB", callback_data="buy_RUB")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_sell_keyboard(exclude_currency):
    buttons = []
    if exclude_currency != "BTC":
        buttons.append([InlineKeyboardButton("Продать BTC", callback_data="sell_BTC")])
    if exclude_currency != "USDT":
        buttons.append([InlineKeyboardButton("Продать USDT", callback_data="sell_USDT")])
    if exclude_currency != "RUB":
        buttons.append([InlineKeyboardButton("Продать RUB", callback_data="sell_RUB")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_buy")])
    return InlineKeyboardMarkup(buttons)

def get_confirmation_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отменить", callback_data="cancel")]])

def get_payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплачено", callback_data="paid")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ])

def get_support_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❓ Связаться с поддержкой", callback_data="support")]])

def get_admin_keyboard():
    if is_bot_working():
        status = "🔴 Выключить бот"  
    else:
        status = "🟢 Включить бот"   
    keyboard = [
        [KeyboardButton("🏦 Реквизиты на подтверждение")], 
        [KeyboardButton("⏳ Ожидают оплаты")],
        [KeyboardButton("💰 Оплаты на подтверждение")],
        [KeyboardButton(f"{status}")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Глобальный словарь для хранения текущих индексов заявок для каждого админа
admin_order_index = {}

def get_pending_requisites_orders():
    """Заявки, ожидающие ввода реквизитов от админа (статус pending_operator)"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.order_id, o.order_number, o.chat_id, o.amount_rub, o.amount_btc, 
               o.buy_currency, o.sell_currency,
               o.client_card_number, o.client_phone_number, o.client_bank_name, o.client_full_name,
               u.first_name, u.username
        FROM orders o
        JOIN users u ON o.chat_id = u.chat_id
        WHERE o.status = 'pending_operator'
        ORDER BY o.created_at ASC
    ''')
    orders = cursor.fetchall()
    conn.close()
    
    result = []
    for order in orders:
        result.append({
            'order_id': order[0],
            'order_number': order[1],
            'chat_id': order[2],
            'amount_rub': order[3],
            'amount_btc': order[4],
            'buy_currency': order[5],
            'sell_currency': order[6],
            'card_number': order[7],
            'phone_number': order[8],
            'bank_name': order[9],
            'full_name': order[10],
            'first_name': order[11] if order[11] else 'Не указан',
            'username': order[12] if order[12] else 'нет'
        })
    return result

def get_pending_payments_orders():
    """Заявки, ожидающие подтверждения оплаты (статус awaiting_confirmation)"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT order_id, order_number, chat_id, amount_rub, amount_btc, buy_currency, sell_currency, receipt_file_id
        FROM orders 
        WHERE status IN ('awaiting_confirmation', 'pending_verification')
        ORDER BY created_at ASC
    ''')
    orders = cursor.fetchall()
    conn.close()
    
    result = []
    for order in orders:
        result.append({
            'order_id': order[0],
            'order_number': order[1],
            'chat_id': order[2],
            'amount_rub': order[3],
            'amount_btc': order[4],
            'buy_currency': order[5],
            'sell_currency': order[6],
            'receipt_file_id': order[7]
        })
    return result

async def show_pending_requisites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает заявки, ожидающие ввода реквизитов"""
    chat_id = update.effective_chat.id
    orders = get_pending_requisites_orders()
    
    if not orders:
        await update.message.reply_text("Нет заявок, ожидающих ввода реквизитов.")
        return
    
    # Сохраняем список заявок в context.user_data
    context.user_data['admin_requisites_orders'] = orders
    context.user_data['admin_requisites_index'] = 0
    
    await show_requisites_order(update, context, 0)

async def show_requisites_order(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    """Показывает конкретную заявку для ввода реквизитов"""
    orders = context.user_data.get('admin_requisites_orders', [])
    if not orders or index >= len(orders):
        return
    
    order = orders[index]

    # Формируем текст в зависимости от валюты продажи
    if order['sell_currency'] == 'RUB':
        amount_text = f"{order['amount_rub']:,.2f} RUB → {order['amount_btc']:.8f} BTC"
    else:
        amount_text = f"{order['amount_btc']:.8f} BTC → {order['amount_rub']:,.2f} RUB"
    
    text = (
        f"📋 Заявка {index + 1} из {len(orders)}\n\n"
        f"📦 {order['order_number']}\n"
        f"👤 {order['first_name']}\n"
        f"🐶 @{order['username']}\n"
        f"💱 {amount_text}\n\n"
        f"📝 Данные клиента:\n"
        f"• Карта: {order['card_number'] or 'Не указан'}\n"
        f"• Телефон: {order['phone_number'] or 'Не указан'}\n"
        f"• Банк: {order['bank_name'] or 'Не указан'}\n"
        f"• ФИО: {order['full_name'] or 'Не указан'}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("◀️", callback_data=f"req_prev_{index}"),
            InlineKeyboardButton("✅ Выбрать", callback_data=f"req_select_{order['order_id']}"),
            InlineKeyboardButton("▶️", callback_data=f"req_next_{index}")
        ]
    ])
    
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=None, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode=None, reply_markup=keyboard)

async def show_pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает заявки, ожидающие подтверждения оплаты"""
    orders = get_pending_payments_orders()
    
    if not orders:
        await update.message.reply_text("Нет заявок, ожидающих подтверждения оплаты.")
        return
    
    context.user_data['admin_payments_orders'] = orders
    context.user_data['admin_payments_index'] = 0
    
    await show_payments_order(update, context, 0)

async def show_payments_order(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    """Показывает конкретную заявку для подтверждения оплаты"""
    orders = context.user_data.get('admin_payments_orders', [])
    if not orders or index >= len(orders):
        return
    
    order = orders[index]
    
    # Получаем данные пользователя из БД (имя, ник)
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, username FROM users WHERE chat_id = ?', (order['chat_id'],))
    user_data = cursor.fetchone()
    conn.close()
    
    first_name = user_data[0] if user_data and user_data[0] else 'Не указан'
    username = user_data[1] if user_data and user_data[1] else 'нет'

    # Формируем текст в зависимости от валюты продажи
    if order['sell_currency'] == 'RUB':
        amount_text = f"{order['amount_rub']:,.2f} RUB → {order['amount_btc']:.8f} BTC"
    else:
        amount_text = f"{order['amount_btc']:.8f} BTC → {order['amount_rub']:,.2f} RUB"
    
    text = (
        f"💰 Заявка {index + 1} из {len(orders)}\n\n"
        f"📦 {order['order_number']}\n"
        f"👤 {first_name}\n"
        f"🐶 @{username}\n"
        f"💱 {amount_text}\n"
        f"📎 Чек: {'загружен ✅' if order['receipt_file_id'] else 'нет ❌'}\n\n"
        f"🕐 Время: {order.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("◀️", callback_data=f"pay_prev_{index}"),
            InlineKeyboardButton("✅ Выбрать", callback_data=f"pay_select_{order['order_id']}"),
            InlineKeyboardButton("▶️", callback_data=f"pay_next_{index}")
        ]
    ])
    
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=None, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode=None, reply_markup=keyboard)

# ===================================================
# ОСНОВНЫЕ ОБРАБОТЧИКИ
# ===================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    update_user_state(chat_id, state='main')
    
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

🤖 Криптообменник

Используйте кнопки внизу экрана для управления.
    """
    await update.message.reply_text(welcome_text, reply_markup=get_admin_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    user_state = get_user_state(chat_id)
    
    # Админ-режим
    if user_state['state'] == 'admin':
        await handle_admin_message(update, context)
        return

# ===================================================
# АДМИН-ПАНЕЛЬ
# ===================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Нет доступа.")
        return
    
    update_user_state(chat_id, state='admin')
    await update.message.reply_text("👋 Админ-панель", reply_markup=get_admin_keyboard())

async def show_pending_order(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int):
    """Показывает конкретную заявку для отклонения"""
    orders = context.user_data.get('admin_pending_orders', [])
    if not orders or index >= len(orders):
        return
    
    order = orders[index]
    
    # Получаем данные пользователя из БД
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, username FROM users WHERE chat_id = ?', (order['chat_id'],))
    user_data = cursor.fetchone()
    conn.close()
    
    first_name = user_data[0] if user_data and user_data[0] else 'Не указан'
    username = user_data[1] if user_data and user_data[1] else 'Не указан'
    
    # Формируем текст в зависимости от валюты продажи
    if order['sell_currency'] == 'RUB':
        amount_text = f"{order['amount_rub']:,.2f} RUB → {order['amount_btc']:.8f} BTC"
    else:
        amount_text = f"{order['amount_btc']:.8f} BTC → {order['amount_rub']:,.2f} RUB"
    
    text = (
        f"💰 Заявка {index + 1} из {len(orders)}\n\n"
        f"📦 {order['order_number']}\n"
        f"👤 {first_name}\n"
        f"🐶 @{username}\n"
        f"💱 {amount_text}\n\n"
        f"🕐 {order.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("◀️", callback_data=f"pend_prev_{index}"),
            InlineKeyboardButton("✅ Выбрать", callback_data=f"pend_select_{order['order_id']}"),
            InlineKeyboardButton("▶️", callback_data=f"pend_next_{index}")
        ]
    ])
    
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=None, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode=None, reply_markup=keyboard)

async def show_pending_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает заявки, ожидающие оплаты (с прокруткой)"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT order_id, order_number, chat_id, amount_rub, amount_btc, sell_currency, buy_currency, status, receipt_file_id FROM orders WHERE status IN ("pending_verification", "awaiting_confirmation", "awaiting_payment") ORDER BY created_at ASC')
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await update.message.reply_text("Нет активных заявок.")
        return
    
    # Преобразуем в список словарей
    orders_list = []
    for order in orders:
        orders_list.append({
            'order_id': order[0],
            'order_number': order[1],
            'chat_id': order[2],
            'amount_rub': order[3],
            'amount_btc': order[4],
            'sell_currency': order[5],
            'buy_currency': order[6],
            'status': order[7],
            'receipt_file_id': order[8],
            'first_name': order[9] if len(order) > 9 else 'Не указан', 
            'username': order[10] if len(order) > 10 else 'нет'         
        })
    
    context.user_data['admin_pending_orders'] = orders_list
    context.user_data['admin_pending_index'] = 0
    
    await show_pending_order(update, context, 0)

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    
        # Обработка ввода реквизитов от админа
    if context.user_data.get('requisites_step'):
        step = context.user_data['requisites_step']
        req_data = context.user_data.get('requisites_data', {})
        
        if step == 'card_number':
            req_data['card_number'] = text
            context.user_data['requisites_step'] = 'bank_name'
            await update.message.reply_text("🏦 Введите название банка:")
        
        elif step == 'bank_name':
            req_data['bank_name'] = text
            context.user_data['requisites_step'] = 'full_name'
            await update.message.reply_text("👤 Введите ФИО получателя:")
        
        elif step == 'full_name':
            req_data['full_name'] = text
            context.user_data['requisites_step'] = 'amount'
            await update.message.reply_text("💰 Введите сумму пополнения (в рублях):")
        
        elif step == 'amount':
            try:
                req_data['amount'] = float(text.replace(',', '.'))
                context.user_data['requisites_step'] = 'confirm'
                
                # Показываем итоговую информацию
                text = (
                    f"📋 **Проверьте введённые реквизиты:**\n\n"
                    f"💳 Номер карты: {req_data.get('card_number')}\n"
                    f"🏦 Банк: {req_data.get('bank_name')}\n"
                    f"👤 ФИО: {req_data.get('full_name')}\n"
                    f"💰 Сумма: {req_data.get('amount'):.2f} ₽\n\n"
                    f"✅ Всё верно?"
                )
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Отправить клиенту", callback_data="send_requisites_to_client")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_requisites")]
                ])
                await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
                context.user_data['requisites_data'] = req_data
            except ValueError:
                await update.message.reply_text("❌ Введите корректное число.")
        
        elif step == 'wallet_address':
            req_data['wallet_address'] = text
            context.user_data['requisites_step'] = 'network'
            await update.message.reply_text("🌐 Введите сеть (например: ERC20, TRC20, Bitcoin):")
        
        elif step == 'network':
            req_data['network'] = text
            context.user_data['requisites_step'] = 'crypto_amount'
            await update.message.reply_text(f"💰 Введите сумму пополнения (в {req_data.get('currency', 'криптовалюте')}):")
        
        elif step == 'crypto_amount':
            try:
                req_data['crypto_amount'] = float(text.replace(',', '.'))
                context.user_data['requisites_step'] = 'confirm_crypto'
                
                text = (
                    f"📋 **Проверьте введённые реквизиты:**\n\n"
                    f"💰 Адрес: {req_data.get('wallet_address')}\n"
                    f"🌐 Сеть: {req_data.get('network')}\n"
                    f"💵 Сумма: {req_data.get('crypto_amount'):.8f}\n\n"
                    f"✅ Всё верно?"
                )
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Отправить клиенту", callback_data="send_requisites_to_client")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_requisites")]
                ])
                await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
                context.user_data['requisites_data'] = req_data
            except ValueError:
                await update.message.reply_text("❌ Введите корректное число.")
        
        context.user_data['requisites_data'] = req_data
        return

    if chat_id not in ADMIN_IDS:
        return
    
    elif text == "⏳ Ожидают оплаты":
        await show_pending_orders(update, context)

    elif text == "🔴 Выключить бот" or text == "🟢 Включить бот":
        new_status = not is_bot_working()
        set_admin_setting('bot_working', str(new_status))
        status_text = "ВКЛЮЧЁН 🟢" if new_status else "ВЫКЛЮЧЕН 🔴"
        await update.message.reply_text(f"Приём заявок {status_text}", reply_markup=get_admin_keyboard())

    elif text == "📊 Курсы":
        keyboard = [
            [InlineKeyboardButton("USD/RUB", callback_data="admin_rate_usd_rub")],
            [InlineKeyboardButton("BTC/USD", callback_data="admin_rate_btc_usd")],
        ]
        await update.message.reply_text("Выберите пару:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "🏦 Реквизиты на подтверждение":
        await show_pending_requisites(update, context)

    elif text == "💰 Оплаты на подтверждение":
        await show_pending_payments(update, context)
    
    elif context.user_data.get('admin_waiting_rate'):
        try:
            rate = float(text.replace(',', '.'))
            pair = context.user_data.get('admin_rate_pair')
            set_admin_setting(pair, str(rate))
            await update.message.reply_text(f"✅ Курс сохранён", reply_markup=get_admin_keyboard())
            context.user_data['admin_waiting_rate'] = False
            context.user_data['admin_rate_pair'] = None
            update_user_state(chat_id, state='admin')
        except ValueError:
            await update.message.reply_text("❌ Введите число.")
        return
    
    elif context.user_data.get('admin_waiting_payment'):
        step = context.user_data.get('admin_payment_step')
        temp = context.user_data.get('admin_payment_temp', {})
        
        if step == 'name':
            temp['name'] = text
            # Если это криптовалюта (BTC или USDT) — сначала запрашиваем сеть
            if temp['currency'] in ['BTC', 'USDT']:
                context.user_data['admin_payment_step'] = 'network'
                await update.message.reply_text("🌐 Укажите сеть транзакции (например: ERC20, TRC20, Bitcoin):")
            else:
                context.user_data['admin_payment_step'] = 'details'
                await update.message.reply_text("📝 Введите реквизиты (номер карты, телефон и т.д.):")
        
        elif step == 'network':
            temp['network'] = text
            context.user_data['admin_payment_step'] = 'address'
            await update.message.reply_text("📋 Введите адрес кошелька:")
        
        elif step == 'address':
            temp['address'] = text
            context.user_data['admin_payment_step'] = 'details'
            await update.message.reply_text("📝 Введите дополнительные реквизиты (при необходимости):")
        
        elif step == 'details':
            temp['details'] = text
            context.user_data['admin_payment_step'] = 'min'
            await update.message.reply_text("📊 Введите минимальную сумму для одной заявки:")
        
        elif step == 'min':
            try:
                temp['min'] = float(text.replace(',', '.'))
                context.user_data['admin_payment_step'] = 'max'
                await update.message.reply_text("📊 Введите максимальную сумму для одной заявки:")
            except ValueError:
                await update.message.reply_text("❌ Введите число.")
        
        elif step == 'max':
            try:
                temp['max'] = float(text.replace(',', '.'))
                context.user_data['admin_payment_step'] = 'total_limit'
                await update.message.reply_text("💰 Введите общий лимит реквизита (сумма, которую можно принять через этот реквизит):")
            except ValueError:
                await update.message.reply_text("❌ Введите число.")
        
        elif step == 'total_limit':
            try:
                temp['total_limit'] = float(text.replace(',', '.'))
                # Сохраняем реквизит
                network = temp.get('network', '')
                address = temp.get('address', '')
                add_payment_detail(
                    temp['currency'], 
                    temp['name'], 
                    network, 
                    address, 
                    temp['details'], 
                    temp['min'], 
                    temp['max'], 
                    temp['total_limit']
                )
                await update.message.reply_text(f"✅ Реквизит добавлен!", reply_markup=get_admin_keyboard())
                context.user_data['admin_waiting_payment'] = False
                context.user_data['admin_payment_step'] = None
                context.user_data['admin_payment_temp'] = None
                update_user_state(chat_id, state='admin')
            except ValueError:
                await update.message.reply_text("❌ Введите число.")
        
        elif context.user_data.get('admin_waiting_limit'):
            try:
                new_limit = float(text.replace(',', '.'))
                currency = context.user_data.get('admin_setting_limit_currency')
                
                # Обновляем total_limit для всех реквизитов этой валюты (пропорционально или просто заменяем?)
                # Проще: добавить отдельную таблицу для лимитов валют, но пока сделаем через admin_settings
                set_admin_setting(f'limit_{currency}', str(new_limit))
                
                await update.message.reply_text(
                    f"✅ Лимит для {currency} установлен: {new_limit:,.2f} руб.",
                    reply_markup=get_admin_keyboard()
                )
                context.user_data['admin_waiting_limit'] = False
                context.user_data['admin_setting_limit_currency'] = None
                update_user_state(chat_id, state='admin')
            except ValueError:
                await update.message.reply_text("❌ Введите число.")
            return

        context.user_data['admin_payment_temp'] = temp
        return
    
async def show_limits_menu(update: Update):
    """Показывает меню с лимитами по валютам"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    
    # Получаем общую капитализацию
    cursor.execute('SELECT SUM(amount) FROM orders WHERE status = "completed"')
    total_cap = cursor.fetchone()[0] or 0
    
    # Получаем лимиты по валютам (сумма всех total_limit из payment_details)
    cursor.execute('''
        SELECT currency, SUM(total_limit) as total, SUM(used_amount) as used 
        FROM payment_details WHERE is_active = 1 GROUP BY currency
    ''')
    limits = cursor.fetchall()
    conn.close()
    
    # Формируем текст
    text = f"📊 **Лимиты и капитализация**\n\n"
    text += f"💰 **Общая капитализация:** {total_cap:,.2f} руб.\n\n"
    text += f"📋 **Лимиты по валютам:**\n"
    
    if limits:
        for limit in limits:
            currency = limit[0]
            available = (limit[1] or 0) - (limit[2] or 0)
            text += f"• {currency}: {available:,.2f} руб.\n"
    else:
        text += "• Нет установленных лимитов\n"
    
    # Создаём инлайн-кнопки для каждой валюты
    keyboard = []
    if limits:
        for limit in limits:
            keyboard.append([InlineKeyboardButton(f"✏️ {limit[0]}", callback_data=f"set_limit_{limit[0]}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_admin")])
    
    await update.message.reply_text(
        text, 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    
    if chat_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ Нет доступа.")
        return
    
    data = query.data
    
    if data == "admin_rate_usd_rub":
        context.user_data['admin_waiting_rate'] = True
        context.user_data['admin_rate_pair'] = 'usd_rub_rate'
        await query.edit_message_text("Введите курс USDT/RUB (например: 92.50):")
    
    elif data == "admin_rate_btc_usd":
        context.user_data['admin_waiting_rate'] = True
        context.user_data['admin_rate_pair'] = 'btc_usd_rate'
        await query.edit_message_text("Введите курс BTC/USDT (например: 65000):")
    
    elif data.startswith("admin_confirm_"):
        order_id = int(data.split("_")[2])
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = "completed" WHERE order_id = ?', (order_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ Заявка {order_id} подтверждена.")
    
    elif data.startswith("admin_reject_"):
        order_id = int(data.split("_")[2])
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = "rejected" WHERE order_id = ?', (order_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"❌ Заявка {order_id} отклонена.")
    
    elif data.startswith("admin_add_"):
        currency = data.split("_")[2].upper()
        context.user_data['admin_waiting_payment'] = True
        context.user_data['admin_payment_step'] = 'name'
        context.user_data['admin_payment_temp'] = {'currency': currency}
        await query.edit_message_text(f"Добавление реквизита для {currency}\n\nВведите название реквизита:")
    
    elif data == "admin_list_payments":
        details = get_payment_details()
        if not details:
            await query.edit_message_text("Нет реквизитов.")
            return
        
        for d in details:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Удалить", callback_data=f"admin_del_payment_{d[0]}")
            ]])
            await query.edit_message_text(
                f"💳 {d[1]}\n{d[2]}\n{d[5]}\n💰 {d[3]} - {d[4]}",
                reply_markup=keyboard
            )
    
    elif data.startswith("admin_del_payment_"):
        detail_id = int(data.split("_")[3])
        delete_payment_detail(detail_id)
        await query.edit_message_text("✅ Реквизит удалён.")

    elif data.startswith("set_limit_"):
        currency = data.split("_")[2]
        context.user_data['admin_setting_limit_currency'] = currency
        await query.edit_message_text(
            f"💰 Введите новый лимит для валюты **{currency}** (в рублях):\n\n"
            f"Лимит означает максимальную сумму заявок, которую можно обработать через реквизиты этой валюты.",
            parse_mode=ParseMode.MARKDOWN
        )
        # Устанавливаем состояние ожидания ввода лимита
        context.user_data['admin_waiting_limit'] = True

        # Навигация по реквизитам
    elif data.startswith("req_prev_"):
        index = int(data.split("_")[2])
        new_index = index - 1
        if new_index >= 0:
            context.user_data['admin_requisites_index'] = new_index
            await show_requisites_order(update, context, new_index)
        else:
            await query.answer("Это первая заявка")

    elif data.startswith("req_next_"):
        index = int(data.split("_")[2])
        orders = context.user_data.get('admin_requisites_orders', [])
        new_index = index + 1
        if new_index < len(orders):
            context.user_data['admin_requisites_index'] = new_index
            await show_requisites_order(update, context, new_index)
        else:
            await query.answer("Это последняя заявка")

    elif data.startswith("req_select_"):
        order_id = int(data.split("_")[2])
        context.user_data['selected_order_id'] = order_id
        context.user_data['selected_order_type'] = 'requisites'
        
        # Получаем текущий текст заявки из сообщения
        current_text = query.message.text
        
        # Меняем только кнопки, текст оставляем тот же
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data=f"req_confirm_{order_id}"),
                InlineKeyboardButton("❌ Отменить", callback_data=f"req_cancel_{order_id}")
            ]
        ])
        await query.edit_message_text(
            text=current_text,
            parse_mode=None,
            reply_markup=keyboard
        )

    elif data.startswith("req_confirm_"):
        order_id = int(data.split("_")[2])
        context.user_data['requisites_order_id'] = order_id
        context.user_data['requisites_step'] = None
        context.user_data['requisites_data'] = {}
        
        # Получаем данные заявки
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT sell_currency, buy_currency, amount_rub, amount_btc FROM orders WHERE order_id = ?', (order_id,))
        order = cursor.fetchone()
        conn.close()
        
        if order and order[0] == 'RUB':
            # Клиент продаёт RUB → нужны реквизиты для пополнения
            await query.edit_message_text(
                "💳 **Введите реквизиты для пополнения (карта получателя):**\n\n"
                "Введите номер карты (пример: 1234 5678 9012 3456):",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['requisites_step'] = 'card_number'
        else:
            # Клиент продаёт BTC или USDT → нужен адрес кошелька
            await query.edit_message_text(
                "💰 **Введите реквизиты для перевода криптовалюты:**\n\n"
                "Введите адрес кошелька:",
                parse_mode=ParseMode.MARKDOWN
            )
            context.user_data['requisites_step'] = 'wallet_address'

    elif data.startswith("req_cancel_"):
        order_id = int(data.split("_")[2])
        update_order_status(order_id, status='cancelled')
        await query.edit_message_text(f"❌ Заявка {order_id} отменена.")
        
        # Обновляем список заявок
        await show_pending_requisites(update, context)

    elif data == "send_requisites_to_client":
        req_data = context.user_data.get('requisites_data', {})
        order_id = context.user_data.get('requisites_order_id')
        
        if not order_id:
            await query.edit_message_text("❌ Ошибка: заявка не найдена.")
            return
        
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        
        # Сохраняем РЕКВИЗИТЫ ОПЕРАТОРА в таблицу orders (в поля operator_*)
        if 'card_number' in req_data:
            cursor.execute('''
                UPDATE orders 
                SET operator_card_number = ?, operator_bank_name = ?, operator_full_name = ?, 
                    operator_rub_amount = ?, status = 'awaiting_payment'
                WHERE order_id = ?
            ''', (req_data.get('card_number'), req_data.get('bank_name'), 
                req_data.get('full_name'), req_data.get('amount'), order_id))
            client_text = (
                f"💳 **Реквизиты для оплаты**\n\n"
                f"💳 Номер карты: `{req_data.get('card_number')}`\n"
                f"🏦 Банк: {req_data.get('bank_name')}\n"
                f"👤 Получатель: {req_data.get('full_name')}\n"
                f"💰 Сумма: {req_data.get('amount'):.2f} ₽\n\n"
                f"⚠️ После перевода нажмите «Оплачено» и загрузите чек.\n\n"
                f"Обратите внимание!\nРеквизиты действительны в течение 30 МИНУТ - далее оплата по ним приниматься не будет!"
                
            )
        else:
            cursor.execute('''
                UPDATE orders 
                SET operator_wallet_address = ?, operator_network = ?, operator_crypto_amount = ?, status = 'awaiting_payment'
                WHERE order_id = ?
            ''', (req_data.get('wallet_address'), req_data.get('network'), 
                req_data.get('crypto_amount'), order_id))
            client_text = (
                f"💰 **Реквизиты для перевода**\n\n"
                f"📋 Адрес: `{req_data.get('wallet_address')}`\n"
                f"🌐 Сеть: {req_data.get('network')}\n"
                f"💵 Сумма: {req_data.get('crypto_amount'):.8f}\n\n"
                f"⚠️ После отправки нажмите «Оплачено».\n\n"
                f"Обратите внимание!\nРеквизиты действительны в течение 30 МИНУТ - далее оплата по ним приниматься не будет!"
            )
        
        cursor.execute('SELECT chat_id FROM orders WHERE order_id = ?', (order_id,))
        result = cursor.fetchone()
        
        if result:
            client_chat_id = result[0]
            
            cursor.execute('''
                INSERT INTO messages_to_send (chat_id, text, reply_markup, created_at)
                VALUES (?, ?, ?, ?)
            ''', (client_chat_id, client_text, 'payment_keyboard', datetime.now().isoformat()))
            
            conn.commit()
            await query.edit_message_text("✅ Реквизиты сохранены! Клиент получит их в ближайшее время.")
        else:
            await query.edit_message_text("❌ Ошибка: клиент не найден.")
        
        conn.close()
        
        context.user_data.pop('requisites_step', None)
        context.user_data.pop('requisites_data', None)
        context.user_data.pop('requisites_order_id', None)

    elif data == "cancel_requisites":
        context.user_data.pop('requisites_step', None)
        context.user_data.pop('requisites_data', None)
        context.user_data.pop('requisites_order_id', None)
        await query.edit_message_text("❌ Ввод реквизитов отменён.")

        # Навигация по оплатам
    elif data.startswith("pay_prev_"):
        index = int(data.split("_")[2])
        new_index = index - 1
        if new_index >= 0:
            context.user_data['admin_payments_index'] = new_index
            await show_payments_order(update, context, new_index)
        else:
            await query.answer("Это первая заявка")

    elif data.startswith("pay_next_"):
        index = int(data.split("_")[2])
        orders = context.user_data.get('admin_payments_orders', [])
        new_index = index + 1
        if new_index < len(orders):
            context.user_data['admin_payments_index'] = new_index
            await show_payments_order(update, context, new_index)
        else:
            await query.answer("Это последняя заявка")

    elif data.startswith("pay_select_"):
        order_id = int(data.split("_")[2])
        context.user_data['selected_order_id'] = order_id
        context.user_data['selected_order_type'] = 'payment'
        
        current_text = query.message.text
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"pay_confirm_{order_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"pay_reject_{order_id}")
            ]
        ])
        await query.edit_message_text(
            text=current_text,
            parse_mode=None,
            reply_markup=keyboard
        )

    elif data.startswith("pay_confirm_"):
        order_id = int(data.split("_")[2])
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = "completed" WHERE order_id = ?', (order_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"✅ Оплата по заявке {order_id} подтверждена!")
        
        # Обновляем список
        await show_pending_payments(update, context)

    elif data.startswith("pay_reject_"):
        order_id = int(data.split("_")[2])
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = "rejected" WHERE order_id = ?', (order_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"❌ Оплата по заявке {order_id} отклонена!")
        
        # Обновляем список
        await show_pending_payments(update, context)

    elif data.startswith("pend_select_"):
        order_id = int(data.split("_")[2])
        context.user_data['selected_order_id'] = order_id
        context.user_data['selected_order_type'] = 'pending'
        
        # Получаем текущий текст заявки из сообщения
        current_text = query.message.text
        
        # Меняем кнопки: теперь только "Отменить"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ Отклонить", callback_data=f"pend_cancel_{order_id}")
            ],
            [
                InlineKeyboardButton("◀️ Назад", callback_data="pend_back")
            ]
        ])
        await query.edit_message_text(
            text=current_text,
            parse_mode=None,
            reply_markup=keyboard
        )

    elif data.startswith("pend_prev_"):
        index = int(data.split("_")[2])
        new_index = index - 1
        if new_index >= 0:
            context.user_data['admin_pending_index'] = new_index
            await show_pending_order(update, context, new_index)
        else:
            await query.answer("Это первая заявка")

    elif data.startswith("pend_next_"):
        index = int(data.split("_")[2])
        orders = context.user_data.get('admin_pending_orders', [])
        new_index = index + 1
        if new_index < len(orders):
            context.user_data['admin_pending_index'] = new_index
            await show_pending_order(update, context, new_index)
        else:
            await query.answer("Это последняя заявка")

    elif data.startswith("pend_cancel_"):
        order_id = int(data.split("_")[2])
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = "rejected" WHERE order_id = ?', (order_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"❌ Заявка {order_id} отклонена!")
        
        # Обновляем список заявок
        await show_pending_orders(update, context)

    elif data == "pend_back":
        # Получаем сохранённый индекс
        index = context.user_data.get('admin_pending_index', 0)
        orders = context.user_data.get('admin_pending_orders', [])
        
        if orders and index < len(orders):
            order = orders[index]
            
            # Формируем текст заявки
            if order['sell_currency'] == 'RUB':
                amount_text = f"{order['amount_rub']:,.2f} RUB → {order['amount_btc']:.8f} BTC"
            else:
                amount_text = f"{order['amount_btc']:.8f} BTC → {order['amount_rub']:,.2f} RUB"
            
            # Получаем имя клиента
            conn = sqlite3.connect('exchange_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT client_full_name FROM users WHERE chat_id = ?', (order['chat_id'],))
            user_data = cursor.fetchone()
            conn.close()
            
            user_name = user_data[0] if user_data and user_data[0] else 'Не указан'
            
            text = (
                f"💰 Заявка {index + 1} из {len(orders)}\n\n"
                f"📦 Номер: {order['order_number']}\n"
                f"👤 Клиент: {user_name}\n"
                f"💱 Обмен: {amount_text}\n"
            )
            
            # Кнопки навигации
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("◀️", callback_data=f"pend_prev_{index}"),
                    InlineKeyboardButton("✅ Выбрать", callback_data=f"pend_select_{order['order_id']}"),
                    InlineKeyboardButton("▶️", callback_data=f"pend_next_{index}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
        else:
            await query.answer("Ошибка: заявка не найдена")

    elif data.startswith("pend_prev_"):
        index = int(data.split("_")[2])
        new_index = index - 1
        if new_index >= 0:
            context.user_data['admin_pending_index'] = new_index
            await show_pending_order(update, context, new_index)
        else:
            await query.answer("Это первая заявка")

    elif data.startswith("pend_next_"):
        index = int(data.split("_")[2])
        orders = context.user_data.get('admin_pending_orders', [])
        new_index = index + 1
        if new_index < len(orders):
            context.user_data['admin_pending_index'] = new_index
            await show_pending_order(update, context, new_index)
        else:
            await query.answer("Это последняя заявка")

    elif data.startswith("pend_cancel_"):
        order_id = int(data.split("_")[2])
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = "rejected" WHERE order_id = ?', (order_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"❌ Заявка {order_id} отклонена!")
        
        # Обновляем список заявок
        await show_pending_orders(update, context)

    elif data == "pend_back":
        # Получаем сохранённый индекс
        index = context.user_data.get('admin_pending_index', 0)
        orders = context.user_data.get('admin_pending_orders', [])
        
        if orders and index < len(orders):
            order = orders[index]
            
            # Формируем текст заявки
            if order['sell_currency'] == 'RUB':
                amount_text = f"{order['amount_rub']:,.2f} RUB → {order['amount_btc']:.8f} BTC"
            else:
                amount_text = f"{order['amount_btc']:.8f} BTC → {order['amount_rub']:,.2f} RUB"
            
            # Получаем имя клиента
            conn = sqlite3.connect('exchange_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT client_full_name FROM users WHERE chat_id = ?', (order['chat_id'],))
            user_data = cursor.fetchone()
            conn.close()
            
            user_name = user_data[0] if user_data and user_data[0] else 'Не указан'
            
            text = (
                f"💰 Заявка {index + 1} из {len(orders)}\n\n"
                f"📦 Номер: {order['order_number']}\n"
                f"👤 Клиент: {user_name}\n"
                f"💱 Обмен: {amount_text}\n"
            )
            
            # Кнопки навигации
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("◀️", callback_data=f"pend_prev_{index}"),
                    InlineKeyboardButton("✅ Выбрать", callback_data=f"pend_select_{order['order_id']}"),
                    InlineKeyboardButton("▶️", callback_data=f"pend_next_{index}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
        else:
            await query.answer("Ошибка: заявка не найдена")  

    elif data == "back_to_admin":
        await query.edit_message_text("👋 Админ-панель", reply_markup=get_admin_keyboard())

async def show_active_orders(update):
    orders = get_active_orders()
    
    if not orders:
        await update.message.reply_text("Нет активных заявок.")
        return
    
    for order in orders:
        order_id, order_number, chat_id, amount_rub, amount_btc, sell_curr, buy_curr, status, first_name, username = order
        
        if sell_curr == 'RUB':
            amount_text = f"{amount_rub:,.2f} RUB → {amount_btc:.8f} BTC"
        else:
            amount_text = f"{amount_btc:.8f} BTC → {amount_rub:,.2f} RUB"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{order[0]}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{order[0]}")
        ]])

        await update.message.reply_text(
            f"📦 {order_number}\n"
            f"👤 {first_name or 'Не указан'} (@{username or 'нет'})\n"
            f"🐶 @{username or 'нет'}\n"
            f"💱 {amount_text}\n"
            f"📌 {status}",
            reply_markup=keyboard
        )

async def show_limits(update: Update):
    """Показывает текущие лимиты и капитализацию"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    
    # Получаем общую капитализацию (сумму всех одобренных заявок)
    cursor.execute('SELECT SUM(amount) FROM orders WHERE status = "completed"')
    total_capitalization = cursor.fetchone()[0] or 0
    
    # Получаем лимиты по реквизитам
    cursor.execute('SELECT currency, SUM(total_limit) - SUM(used_amount) FROM payment_details WHERE is_active = 1 GROUP BY currency')
    payment_limits = cursor.fetchall()
    
    conn.close()
    
    text = f"💳 **Лимиты и капитализация**\n\n"
    text += f"📊 **Общая капитализация:** {total_capitalization:,.2f} руб.\n\n"
    text += f"📋 **Доступные лимиты по реквизитам:**\n"
    
    if payment_limits:
        for limit in payment_limits:
            text += f"• {limit[0]}: {limit[1]:,.2f}\n"
    else:
        text += "• Нет активных реквизитов\n"
    
    text += f"\n🕐 *Обновлено:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())

# ===================================================
# ЗАПУСК
# ===================================================

def main():
    init_db()
    
    TOKEN = 'your_token'
    
    request = HTTPXRequest(connect_timeout=60, read_timeout=60)
    application = Application.builder().token(TOKEN).request(request).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern='^(admin_|set_rate_|add_|list_payments|del_payment_|confirm_|reject_|req_|pay_|send_|cancel_|pend_)'))
    
    print('🤖 Бот запущен!')
    print('Админ-панель: /admin')
    
    application.run_polling()

if __name__ == '__main__':
    main()