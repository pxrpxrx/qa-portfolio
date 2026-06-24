import requests
import sqlite3
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import threading
import time
import asyncio

OPERATOR_CHANNEL_ID = -1003902263934

# Конфигурация BestChange API (прямые запросы)
API_KEY = "YOUR_API"
BASE_URL = "https://bestchange.app/v2"

BTC_ID = 93
USDT_ID = 10   # Tether TRC20
RUB_ID = 105   # Российский рубль
MY_EXCHANGER_ID = 1029  # Твой ID обменника

def is_bot_working():
    """Проверяет, работает ли бот (читает настройку из admin_settings)"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM admin_settings WHERE key = "bot_working"')
    result = cursor.fetchone()
    conn.close()
    return result[0] == 'True' if result else True

def get_bestchange_rate(from_id, to_id, exchanger_id=None):
    """Получает курс с BestChange для конкретного обменника или лучший"""
    url = f"{BASE_URL}/{API_KEY}/rates/{from_id}-{to_id}"
    resp = requests.get(url)
    data = resp.json()
    
    pair_key = f"{from_id}-{to_id}"
    rates = data.get('rates', {}).get(pair_key, [])
    
    if not rates:
        return None
    
    if exchanger_id is not None:
        for rate in rates:
            if rate.get('changer') == exchanger_id:
                selected = rate
                break
        else:
            selected = rates[0]
    else:
        selected = rates[0]
    
    rate_raw = float(selected['rate'])
    real_rate = 1 / rate_raw if rate_raw < 1 else rate_raw
    
    return {
        'rate': real_rate,
        'reserve': float(selected.get('reserve', 0)),
        'min': float(selected.get('inmin', 0)),
        'max': float(selected.get('inmax', 0)),
        'exchanger_id': selected.get('changer')
    }

def get_btc_usdt():
    result = get_bestchange_rate(BTC_ID, USDT_ID, MY_EXCHANGER_ID)
    return result['rate'] if result else None

'''def get_btc_rub():
    result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
    return result['rate'] if result else None'''

def get_btc_rub():
    """Получает курс BTC/RUB из кэша БД"""
    cached = get_cached_rate('BTC', 'RUB')
    if cached:
        return cached['rate']
    
    # Если кэш пуст (первый запуск), получаем напрямую
    result = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
    if result:
        save_rate_to_cache('BTC', 'RUB', result)
        return result['rate']
    return None

def get_usdt_rub():
    btc_usdt = get_btc_usdt()
    btc_rub = get_btc_rub()
    if btc_usdt and btc_rub:
        return btc_rub / btc_usdt
    return None

def get_rate(currency_from, currency_to):
    """Получает курс через BestChange"""
    if currency_from == 'BTC' and currency_to == 'RUB':
        return get_btc_rub()
    elif currency_from == 'RUB' and currency_to == 'BTC':
        rate = get_btc_rub()
        return 1 / rate if rate else None
    return None

def init_db():
    """Создаёт таблицы для хранения состояний и заявок"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cached_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency_from TEXT,
            currency_to TEXT,
            rate REAL,
            reserve REAL,
            min_amount REAL,
            max_amount REAL,
            exchanger_id INTEGER,
            updated_at TEXT
        )
    ''')
    
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
    
    conn.commit()
    conn.close()

def start_rate_updater():
    """Запускает фоновый поток для обновления курсов каждую минуту"""
    
    def update_loop():
        while True:
            try:
                update_all_rates_to_cache()
            except Exception as e:
                print(f"❌ Ошибка обновления курсов: {e}")
            time.sleep(60)  # Ждём 60 секунд перед следующим обновлением
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    print("🚀 Фоновый обновлятор курсов запущен (каждые 60 секунд)")

# ===================================================
# КЭШ КУРСОВ
# ===================================================

def get_cached_rate(currency_from, currency_to):
    """Получает курс из кэша БД"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rate, reserve, min_amount, max_amount, updated_at 
        FROM cached_rates 
        WHERE currency_from = ? AND currency_to = ?
    ''', (currency_from, currency_to))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'rate': result[0],
            'reserve': result[1],
            'min': result[2],
            'max': result[3],
            'updated_at': result[4]
        }
    return None

def save_rate_to_cache(currency_from, currency_to, rate_data):
    """Сохраняет курс в кэш БД"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO cached_rates 
        (currency_from, currency_to, rate, reserve, min_amount, max_amount, exchanger_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        currency_from, currency_to,
        rate_data['rate'],
        rate_data['reserve'],
        rate_data['min'],
        rate_data['max'],
        rate_data['exchanger_id'],
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def update_all_rates_to_cache():
    """Обновляет все курсы в кэше (вызывается фоновым потоком)"""
    print("🔄 Обновление курсов в кэше...")
    
    # BTC -> RUB
    btc_rub = get_bestchange_rate(BTC_ID, RUB_ID, MY_EXCHANGER_ID)
    if btc_rub:
        save_rate_to_cache('BTC', 'RUB', btc_rub)
        print(f"   BTC/RUB: {btc_rub['rate']:.2f}")
    
    print("✅ Курсы обновлены")

def get_user_state(chat_id):
    """Получает состояние пользователя со всеми полями"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT state, buy_currency, sell_currency, current_order_id,
               client_card_number, client_phone_number, client_bank_name, client_full_name, first_name, username 
        FROM users WHERE chat_id = ?
    ''', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'state': result[0], 
            'buy_currency': result[1], 
            'sell_currency': result[2], 
            'current_order_id': result[3],
            'client_card_number': result[4],
            'client_phone_number': result[5],
            'client_bank_name': result[6],
            'client_full_name': result[7],
            'first_name': result[8],
            'username': result[9]
        }
    return {
        'state': 'main', 
        'buy_currency': None, 
        'sell_currency': None, 
        'current_order_id': None,
        'client_card_number': None,
        'client_phone_number': None,
        'client_bank_name': None,
        'client_full_name': None,
        'first_name': None,
        'username': None
    }

def update_user_state(chat_id, state=None, buy_currency=None, sell_currency=None, current_order_id=None,
                      client_card_number=None, client_phone_number=None, client_bank_name=None, client_full_name=None, first_name=None, username=None):
    """Обновляет состояние пользователя"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT state FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    
    if not result:
        cursor.execute('''
            INSERT INTO users (chat_id, state, buy_currency, sell_currency, current_order_id,
                               client_card_number, client_phone_number, client_bank_name, client_full_name, first_name, username) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, state or 'main', buy_currency, sell_currency, current_order_id,
              client_card_number, client_phone_number, client_bank_name, client_full_name, first_name, username))
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
        if client_card_number is not None:
            updates.append('client_card_number = ?')
            params.append(client_card_number)
        if client_phone_number is not None:
            updates.append('client_phone_number = ?')
            params.append(client_phone_number)
        if client_bank_name is not None:
            updates.append('client_bank_name = ?')
            params.append(client_bank_name)
        if client_full_name is not None:
            updates.append('client_full_name = ?')
            params.append(client_full_name)
        if first_name is not None:
            updates.append('first_name = ?')
            params.append(first_name)
        if username is not None:
            updates.append('username = ?')
            params.append(username)    
        
        if updates:
            params.append(chat_id)
            cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE chat_id = ?', params)
    
    conn.commit()
    conn.close()

def create_order(chat_id, buy_currency, sell_currency, amount_rub, amount_btc):
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
        INSERT INTO orders (chat_id, order_number, buy_currency, sell_currency, amount_rub, amount_btc, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, order_number, buy_currency, sell_currency, amount_rub, amount_btc, datetime.now().isoformat()))
    
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

# ===================================================
# КЛАВИАТУРЫ
# ===================================================

def get_main_keyboard():
    """Создаёт главную Reply Keyboard"""
    keyboard = [
        [KeyboardButton("➕ Создать обмен")],
        [KeyboardButton("📊 Курсы и лимиты")],
        [KeyboardButton("📋 Мои заявки / Статус")],
        [KeyboardButton("❓ Поддержка")],
        [KeyboardButton("🔒 Правила AML/KYC")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_buy_keyboard():
    """Клавиатура выбора валюты покупки"""
    keyboard = [
        [InlineKeyboardButton("₿ Купить BTC", callback_data="buy_BTC")],
        #[InlineKeyboardButton("$ Купить USDT", callback_data="buy_USDT")],
        [InlineKeyboardButton("₽ Купить RUB", callback_data="buy_RUB")]
    ]
    return InlineKeyboardMarkup(keyboard)

'''
def get_sell_keyboard(exclude_currency):
    """Клавиатура выбора валюты продажи (исключая выбранную для покупки)"""
    buttons = []
    if exclude_currency != "BTC":
        buttons.append([InlineKeyboardButton("₿ Продать BTC", callback_data="sell_BTC")])
    if exclude_currency != "USDT":
        buttons.append([InlineKeyboardButton("$ Продать USDT", callback_data="sell_USDT")])
    if exclude_currency != "RUB":
        buttons.append([InlineKeyboardButton("₽ Продать RUB", callback_data="sell_RUB")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_buy")])
    return InlineKeyboardMarkup(buttons)
'''
    
def get_confirmation_keyboard():
    """Клавиатура для подтверждения"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    """Клавиатура для оплаты"""
    keyboard = [
        [InlineKeyboardButton("💳 Оплачено", callback_data="paid")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_support_keyboard():
    """Клавиатура с поддержкой"""
    keyboard = [[InlineKeyboardButton("❓ Связаться с поддержкой", callback_data="support")]]
    return InlineKeyboardMarkup(keyboard)

# ===================================================
# ОБРАБОТЧИКИ
# ===================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    update_user_state(chat_id, state='main', first_name=user.first_name, username=user.username)
    
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

🤖 **Криптообменник**

*Change crypto. Change perspective. Never change your principles.*

Используйте кнопки внизу экрана для управления.
    """
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки главного меню"""
    text = update.message.text
    chat_id = update.effective_chat.id
    user_state = get_user_state(chat_id)

    # Проверка статуса работы бота
    if not is_bot_working():
        await update.message.reply_text(
            "⛔ Обменник временно не работает.\n\n"
            "По всем вопросам обращайтесь в поддержку: @support_bot"
        )
        return
    user_state = get_user_state(chat_id)
    
    if text == "➕ Создать обмен":
        await create_exchange(update, chat_id)

    elif user_state['state'] == 'awaiting_card_number':
        update_user_state(chat_id, client_card_number=text, state='awaiting_phone_number')
        await update.message.reply_text("📱 Введите номер телефона, привязанный к карте:")
        return
    
    elif user_state['state'] == 'awaiting_phone_number':
        update_user_state(chat_id, client_phone_number=text, state='awaiting_bank_name')
        await update.message.reply_text("🏦 Введите название банка:")
        return
    
    elif user_state['state'] == 'awaiting_bank_name':
        update_user_state(chat_id, client_bank_name=text, state='awaiting_full_name')
        await update.message.reply_text("👤 Введите ФИО владельца карты:")
        return
    
    elif user_state['state'] == 'awaiting_full_name':
        update_user_state(chat_id, 
            client_card_number=user_state.get('client_card_number'),
            client_phone_number=user_state.get('client_phone_number'),
            client_bank_name=user_state.get('client_bank_name'),
            client_full_name=text,
            state='confirming_payment_data')
        
        # Получаем обновлённое состояние пользователя
        user = get_user_state(chat_id)
        order_id = user.get('current_order_id')
        
        # Получаем данные заявки
        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT amount_rub, amount_btc, buy_currency, sell_currency FROM orders WHERE order_id = ?', (order_id,))
        order = cursor.fetchone()
        conn.close()
        
        if not order:
            await update.message.reply_text("❌ Ошибка: заявка не найдена.")
            return
        
        amount_rub = order[0]
        amount_btc = order[1]   
        buy_curr = order[2]     
        sell_curr = order[3]    
        
        rate = get_rate(sell_curr, buy_curr)

        # Формируем текст в зависимости от направления
        if sell_curr == 'RUB':
            # Продаём рубли, покупаем BTC
            amount_text = f"{amount_rub:,.2f} {sell_curr}"
            converted_text = f"{amount_btc:.8f} {buy_curr}"
        else:  # sell_curr == 'BTC'
            # Продаём BTC, покупаем рубли
            amount_text = f"{amount_btc:.8f} {sell_curr}"
            converted_text = f"{amount_rub:,.2f} {buy_curr}"        
        
        text = (
            f"📋 **Проверьте введённые данные:**\n\n"
            f"💱 Сумма: {amount_text} → {buy_curr}\n"
            f"💰 Курс: 1 {sell_curr} = {rate:.8f} {buy_curr}\n"
            f"💵 К получению: {converted_text}\n\n"
            f"💳 Данные карты:\n"
            f"• Номер карты: {user.get('client_card_number')}\n"
            f"• Телефон: {user.get('client_phone_number')}\n"
            f"• Банк: {user.get('client_bank_name')}\n"
            f"• ФИО: {user.get('client_full_name')}\n\n"
            f"✅ Всё верно?"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_payment_data")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_payment_data")]
        ])
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        return
    
    elif text == "📊 Курсы и лимиты":
        await show_rates(update)
    
    elif text == "📋 Мои заявки / Статус":
        await show_my_orders(update, chat_id)
    
    elif text == "❓ Поддержка":
        await show_support(update)
    
    elif text == "🔒 Правила AML/KYC":
        await show_aml_kyc(update)
    
    else:
        # Обработка ввода суммы
        state = get_user_state(chat_id)
        if state['state'] == 'awaiting_amount':
            try:
                amount = float(text.replace(',', '.'))
                await process_amount(update, chat_id, amount)
            except ValueError:
                await update.message.reply_text("❌ Пожалуйста, введите корректное число.")
        else:
            await update.message.reply_text(
                "Пожалуйста, используйте кнопки внизу экрана.",
                reply_markup=get_main_keyboard()
            )

async def create_exchange(update, chat_id):
    """Начинает процесс создания обмена"""
    update_user_state(chat_id, state='awaiting_buy')
    await update.message.reply_text(
        "💰 **Какую валюту планируете купить?**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_buy_keyboard()
    )

async def show_rates(update):
    btc_rub = get_btc_rub()
    
    if btc_rub:
        text = (
            f"📊 **Актуальные курсы**\n\n"
            f"💰 1 BTC = {btc_rub:,.2f} RUB\n\n"
            f"📋 **Лимиты:**\n"
            f"• Минимальная сумма: 0.001 BTC / 500 RUB\n"
            f"• Максимальная сумма: 5 BTC / 5000000 RUB"
        )
    else:
        text = "❌ Не удалось получить курсы. Попробуйте позже."
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())

async def show_my_orders(update, chat_id):
    """Показывает заявки пользователя"""
    conn = sqlite3.connect('exchange_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT order_number, buy_currency, sell_currency, amount, status, created_at FROM orders WHERE chat_id = ? ORDER BY created_at DESC LIMIT 10', (chat_id,))
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        await update.message.reply_text("📋 У вас пока нет заявок.", reply_markup=get_main_keyboard())
        return
    
    text = "📋 Ваши заявки:\n\n"
    for order in orders:
        status_emoji = "⏳" if order[4] == 'pending' else "✅" if order[4] == 'completed' else "❌"
        text += f"{status_emoji} {order[0]}: {order[3]} {order[2]} → {order[1]} ({order[4]})\n"
    
    await update.message.reply_text(text, reply_markup=get_main_keyboard())

async def show_support(update):
    """Показывает контакты поддержки"""
    await update.message.reply_text(
        "❓ Поддержка\n\n"
        "По всем вопросам обращайтесь:\n"
        "✉️ Email: support@your_site.com\n"
        "📱 Telegram: @your_support\n\n"
        "Ответ в течение 15 минут в рабочее время.",
        reply_markup=get_main_keyboard()
    )

async def show_aml_kyc(update):
    """Показывает правила AML/KYC"""
    await update.message.reply_text(
        "🔒 **Правила AML/KYC**\n\n"
        "• **KYC** — обязательная верификация для сумм от 10 000 ₽\n"
        "• **AML** — проверка транзакций на легальность\n"
        "• Все обмены проходят через гаранта\n"
        "• Данные пользователей защищены",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ===================================================
# ОБРАБОТЧИКИ INLINE КНОПОК
# ===================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на инлайн-кнопки"""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    data = query.data
    user_state = get_user_state(chat_id)
    
    '''if data.startswith("buy_"):
        currency = data.split("_")[1]
        update_user_state(chat_id, buy_currency=currency, state='awaiting_sell')
        await query.edit_message_text(
            f"✅ Вы выбрали покупку **{currency}**\n\n"
            f"💸 **Какую валюту планируете продать?**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_sell_keyboard(currency)
        )'''
    
    # Проверка статуса работы бота
    if not is_bot_working():
        await query.edit_message_text(
            "⛔ Обменник временно не работает.\n\n"
            "По всем вопросам обращайтесь в поддержку: @your_support"
        )
        return
    data = query.data
    user_state = get_user_state(chat_id)
    
    if data.startswith("buy_"):
        currency = data.split("_")[1]
        
        # Сохраняем выбранную валюту покупки
        update_user_state(chat_id, buy_currency=currency)
        
        # Определяем валюту продажи (противоположная)
        if currency == "BTC":
            sell_currency = "RUB"
            update_user_state(chat_id, sell_currency=sell_currency)
            rate_raw = get_rate(sell_currency, currency)
            if rate_raw:
                # Преобразуем в 1 BTC = X RUB
                rate = 1 / rate_raw
                formatted_rate = f"{rate:,.2f}"
                rate_text = f"1 BTC = {formatted_rate} ₽"
        else:  # currency == "RUB"
            sell_currency = "BTC"
            update_user_state(chat_id, sell_currency=sell_currency)
            rate = get_rate(sell_currency, currency)
            if rate:
                formatted_rate = f"{rate:,.2f}"
                rate_text = f"1 BTC = {formatted_rate} ₽"
        
        if rate:
            await query.edit_message_text(
                f"📊 **Подтверждение обмена**\n\n"
                f"Покупка: **{currency}**\n"
                f"Продажа: **{sell_currency}**\n"
                f"{rate_text}\n\n"
                f"Введите сумму в **{sell_currency}**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_confirmation_keyboard()
            )
            update_user_state(chat_id, state='awaiting_amount')
        else:
            await query.edit_message_text(
                "❌ Не удалось получить курс. Попробуйте позже.",
                reply_markup=get_buy_keyboard()
            )
            update_user_state(chat_id, state='awaiting_buy')
    
    elif data.startswith("sell_"):
        currency = data.split("_")[1]
        update_user_state(chat_id, sell_currency=currency, state='confirming')
        user_state = get_user_state(chat_id)
        buy_curr = user_state['buy_currency']
        sell_curr = user_state['sell_currency']
        print(f"DEBUG: buy_curr={buy_curr}, sell_curr={sell_curr}")
        rate = get_rate(sell_curr, buy_curr)
        
        if rate:
            await query.edit_message_text(
                f"📊 **Подтверждение обмена**\n\n"
                f"Покупка: **{buy_curr}**\n"
                f"Продажа: **{sell_curr}**\n"
                f"Курс: 1 {sell_curr} = {rate:.10f} {buy_curr}\n\n"
                f"Для продолжения введите сумму в **{sell_curr}**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_confirmation_keyboard()
            )
            update_user_state(chat_id, state='awaiting_amount')
        else:
            await query.edit_message_text(
                "❌ Не удалось получить курс для этой пары. Попробуйте позже.",
                reply_markup=get_buy_keyboard()
            )
            update_user_state(chat_id, state='awaiting_buy')
    
    elif data == "confirm":
        await query.edit_message_text(
            "💸 **Введите сумму обмена:**\n"
            f"(в {user_state['sell_currency']})",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=None
        )
        update_user_state(chat_id, state='awaiting_amount')
    
    elif data == "back_to_buy":
        update_user_state(chat_id, state='awaiting_buy')
        await query.edit_message_text(
            "💰 **Какую валюту планируете купить?**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_buy_keyboard()
        )
    
    elif data == "paid":
        await process_payment(update, chat_id, query)
    
    elif data == "support":
        support_text = (
            "❓ Служба поддержки\n\n"
            "Напишите нам: @??????\n"
            "Или отправьте сообщение сюда, мы ответим."
        )
        await query.edit_message_text(support_text)

    elif data == "confirm_payment_data":
        user_state = get_user_state(chat_id)
        order_id = user_state.get('current_order_id')
        user = update.effective_user
        user_name = user.first_name
        user_username = f"@{user.username}" if user.username else "нет"

        conn = sqlite3.connect('exchange_bot.db')
        cursor = conn.cursor()
        
        # ИСПРАВЛЕНО: amount_rub, amount_btc вместо amount
        cursor.execute('''
            SELECT amount_rub, amount_btc, buy_currency, sell_currency, order_number,
                client_card_number, client_phone_number, client_bank_name, client_full_name
            FROM orders WHERE order_id = ?
        ''', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            await query.edit_message_text("❌ Ошибка: заявка не найдена.")
            conn.close()
            return
        
        amount_rub = order[0]
        amount_btc = order[1]
        buy_curr = order[2]
        sell_curr = order[3]
        order_number = order[4]
        client_card = order[5] or user_state.get('client_card_number')
        client_phone = order[6] or user_state.get('client_phone_number')
        client_bank = order[7] or user_state.get('client_bank_name')
        client_name = order[8] or user_state.get('client_full_name')
        
        # Обновляем реквизиты клиента в orders
        cursor.execute('''
            UPDATE orders 
            SET client_card_number = ?, client_phone_number = ?, client_bank_name = ?, client_full_name = ?
            WHERE order_id = ?
        ''', (client_card, client_phone, client_bank, client_name, order_id))
        
        conn.commit()
        
        # Формируем текст суммы в зависимости от валюты продажи
        if sell_curr == 'RUB':
            amount_text = f"{amount_rub:,.2f} {sell_curr} → {amount_btc:.8f} {buy_curr}"
        else:
            amount_text = f"{amount_btc:.8f} {sell_curr} → {amount_rub:,.2f} {buy_curr}"
        
        # Отправляем в канал оператора
        operator_text = (
            f"🆕 НОВАЯ ЗАЯВКА НА ОБМЕН\n\n"
            f"📦 Заявка: `{order_number}`\n"
            f"👤 {user_name}\n"
            f"🐶 {user_username}\n"
            f"💱 {amount_text}\n\n"
            f"💳 Реквизиты КЛИЕНТА:\n"
            f"• Карта: {client_card or 'Не указан'}\n"
            f"• Телефон: {client_phone or 'Не указан'}\n"
            f"• Банк: {client_bank or 'Не указан'}\n"
            f"• ФИО: {client_name or 'Не указан'}\n\n"
            f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await context.bot.send_message(chat_id=OPERATOR_CHANNEL_ID, text=operator_text)
        
        conn.close()
        
        update_order_status(order_id, status='pending_operator')
        update_user_state(chat_id, state='main', buy_currency=None, sell_currency=None, current_order_id=None)
        
        await query.edit_message_text(
            "✅ **Заявка отправлена на проверку оператору!**\n\n"
            "Ожидайте подтверждения в течение 15 минут.\n\n"
            "По вопросам — кнопка «Поддержка».",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_support_keyboard()
        )

    elif data == "cancel_payment_data":
        update_user_state(chat_id, state='main', buy_currency=None, sell_currency=None, current_order_id=None)
        await query.edit_message_text(
            "❌ Ввод данных отменён.\n\n"
            "Вы можете начать новый обмен, нажав кнопку «Создать обмен».",
            reply_markup=get_main_keyboard()
        )
    
    elif data == "cancel":
        update_user_state(chat_id, state='main', buy_currency=None, sell_currency=None, current_order_id=None)
        await query.edit_message_text(
            "❌ Заявка отменена\n\n"
            "Вы можете начать новый обмен, нажав кнопку «Создать обмен» внизу экрана."
        )
        await update.effective_chat.send_message(
            text="",
            reply_markup=get_main_keyboard()
        )


async def process_amount(update, chat_id, amount):
    user_state = get_user_state(chat_id)
    sell_curr = user_state['sell_currency']
    buy_curr = user_state['buy_currency']
    rate = get_rate(sell_curr, buy_curr)
    
    if not rate:
        await update.message.reply_text("❌ Ошибка получения курса.", reply_markup=get_main_keyboard())
        update_user_state(chat_id, state='main')
        return
    
    # Рассчитываем суммы в разных валютах
    if sell_curr == "RUB":
        amount_rub = amount
        amount_btc = amount * rate if rate else 0
    else:  # sell_curr == "BTC"
        amount_btc = amount
        amount_rub = amount * rate if rate else 0    
    
    order_id, order_number = create_order(chat_id, buy_curr, sell_curr, amount_rub, amount_btc)
    update_user_state(chat_id, current_order_id=order_id)
    converted_amount = amount * rate
    
    if sell_curr == "RUB":
        # Продаём рубли → запрашиваем данные
        update_user_state(chat_id, state='awaiting_card_number')
        await update.message.reply_text(
            "💳 **Введите номер карты**, с которой будет произведён перевод (пример: 1234 5678 9012 3456):",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await show_crypto_payment_details(update, chat_id, amount_btc, amount_rub, sell_curr, order_number)
    

async def show_crypto_payment_details(update, chat_id, amount_btc, amount_rub, sell_currency, order_number):
    """Показывает адрес кошелька для крипто-перевода"""
    # В реальном проекте здесь генерируется новый адрес для каждой заявки
    crypto_addresses = {
        "BTC": "bc_your_address",
        "USDT": "0x_your_wallet_address"
    }
    networks = {
        "BTC": "Bitcoin (BTC)",
        "USDT": "ERC20 (Ethereum)"
    }
    
    text = (
        f"💸 **Реквизиты для перевода**\n\n"
        f"Заявка: `{order_number}`\n"
        f"К отправке: **{amount_btc:.8f} {sell_currency}**\n"
        f"Получите: **{amount_rub:.2f} RUB**\n\n"
        f"📋 **Адрес для перевода:**\n"
        f"`{crypto_addresses[sell_currency]}`\n\n"
        f"🌐 **Сеть:** {networks[sell_currency]}\n\n"
        f"⚠️ Отправьте точную сумму и нажмите «Оплачено»."
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_payment_keyboard())

async def process_payment(update, chat_id, query):
    """Обрабатывает нажатие кнопки 'Оплачено'"""
    user_state = get_user_state(chat_id)
    order_id = user_state.get('current_order_id')

    # Проверка статуса работы бота
    if not is_bot_working():
        await query.edit_message_text(
            "⛔ Обменник временно не работает.\n\n"
            "По всем вопросам обращайтесь в поддержку: @your_support"
        )
        return
    
    if order_id:
        update_order_status(order_id, status='awaiting_confirmation')
        update_user_state(chat_id, state='awaiting_confirmation')
    
    await query.edit_message_text(
        "📎 **Загрузите чек, подтверждающий оплату**\n\n"
        "Формат: PDF, фото или скриншот\n\n"
        "После загрузки мы проверим транзакцию.",
        parse_mode=ParseMode.MARKDOWN
    ) 

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает загрузку чеков"""
    chat_id = update.effective_chat.id
    user_state = get_user_state(chat_id)
    user = update.effective_user
    
    if user_state['state'] == 'awaiting_confirmation':
        document = update.message.document
        file_id = document.file_id
        order_id = user_state.get('current_order_id')
        
        if order_id:
            update_order_status(order_id, status='pending_verification', receipt_file_id=file_id)
        
        # ⬇️ ПЕРЕСЫЛКА В КАНАЛ ОПЕРАТОРА ⬇️
        try:
            # Получаем данные заявки
            order_number = None
            conn = sqlite3.connect('exchange_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT order_number, buy_currency, sell_currency, amount_rub, amount_btc FROM orders WHERE order_id = ?', (order_id,))
            order_data = cursor.fetchone()
            conn.close()
            
            if order_data:
                order_number, buy_curr, sell_curr, amount_rub, amount_btc = order_data

            # Формируем строку суммы в зависимости от валюты
            if sell_curr == 'RUB':
                amount_text = f"{amount_rub:,.2f} {sell_curr} → {amount_btc:.8f} {buy_curr}"
            else:  # BTC
                amount_text = f"{amount_btc:,.8f} {sell_curr} → {amount_rub:.2f} {buy_curr}"            
            
            # Создаём подпись
            caption = (
                f"📎 НОВЫЙ ЧЕК ОТ ПОЛЬЗОВАТЕЛЯ\n\n"
                f"📦 Заявка: {order_number}\n"
                f"👤 {user.first_name}\n"
                f"🐶 @{user.username if user.username else 'нет'}\n"
                f"💱 {amount_text}\n\n"
                f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Отправляем документ в канал оператора
            await context.bot.send_document(
                chat_id=OPERATOR_CHANNEL_ID,
                document=file_id,
                caption=caption
            )
            print(f"✅ Документ переслан в канал оператора")
        except Exception as e:
            print(f"❌ Ошибка пересылки документа в канал: {e}")
        # ⬆️ КОНЕЦ БЛОКА ПЕРЕСЫЛКИ ⬆️
        
        update_user_state(chat_id, state='main', buy_currency=None, sell_currency=None, current_order_id=None)
        
        await update.message.reply_text(
            "✅ Чек получен!\n\n"
            "⏳ Ожидайте подтверждения в течение 15 минут.\n\n"
            "По всем вопросам — кнопка «Поддержка».",
            reply_markup=get_support_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ У вас нет активных заявок.\n\n"
            "Начните создание обмена через кнопку «➕ Создать обмен».",
            reply_markup=get_main_keyboard()
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает загрузку фото вместо документа"""
    chat_id = update.effective_chat.id
    user_state = get_user_state(chat_id)
    user = update.effective_user
    
    if user_state['state'] == 'awaiting_confirmation':
        photo = update.message.photo[-1]
        file_id = photo.file_id
        order_id = user_state.get('current_order_id')
        
        if order_id:
            update_order_status(order_id, status='pending_verification', receipt_file_id=file_id)
        
        # ⬇️ ПЕРЕСЫЛКА В КАНАЛ ОПЕРАТОРА ⬇️
        try:
            # Получаем данные заявки для информации
            order_number = None
            conn = sqlite3.connect('exchange_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT order_number, buy_currency, sell_currency, amount_rub, amount_btc FROM orders WHERE order_id = ?', (order_id,))
            order_data = cursor.fetchone()
            conn.close()
            
            if order_data:
                order_number, buy_curr, sell_curr, amount_rub, amount_btc = order_data
            
            # Формируем строку суммы в зависимости от валюты
            if sell_curr == 'RUB':
                amount_text = f"{amount_rub:,.2f} {sell_curr} → {amount_btc:.8f} {buy_curr}"
            else:  # BTC
                amount_text = f"{amount_btc:,.8f} {sell_curr} → {amount_rub:.2f} {buy_curr}"

            # Создаём подпись для оператора
            caption = (
                f"📎 НОВЫЙ ЧЕК ОТ ПОЛЬЗОВАТЕЛЯ\n\n"
                f"📦 Заявка: `{order_number}`\n"
                f"👤 {user.first_name}\n"
                f"🐶 @{user.username if user.username else 'нет'}\n"
                f"💱 {amount_text}\n\n"
                f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Отправляем фото в канал оператора
            await context.bot.send_photo(
                chat_id=OPERATOR_CHANNEL_ID,
                photo=file_id,
                caption=caption
            )
            print(f"✅ Фото переслано в канал оператора")
        except Exception as e:
            print(f"❌ Ошибка пересылки фото в канал: {e}")
        # ⬆️ КОНЕЦ БЛОКА ПЕРЕСЫЛКИ ⬆️
        
        update_user_state(chat_id, state='main', buy_currency=None, sell_currency=None, current_order_id=None)
        
        await update.message.reply_text(
            "✅ Чек получен!\n\n"
            "⏳ Ожидайте подтверждения в течение 15 минут.\n\n"
            "По всем вопросам — кнопка «Поддержка».",
            reply_markup=get_support_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ У вас нет активных заявок.",
            reply_markup=get_main_keyboard()
        )

async def send_pending_messages(app: Application):
    """Проверяет и отправляет ожидающие сообщения (запускается в отдельном потоке)"""
    
    def check_loop():
        while True:
            try:
                conn = sqlite3.connect('exchange_bot.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, chat_id, text FROM messages_to_send WHERE sent = 0')
                messages = cursor.fetchall()
                
                for msg_id, chat_id, text in messages:
                    try:
                        # Используем существующий app для отправки
                        app.bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=get_payment_keyboard()
                        )
                        cursor.execute('UPDATE messages_to_send SET sent = 1 WHERE id = ?', (msg_id,))
                        print(f"✅ Сообщение отправлено пользователю {chat_id}")
                    except Exception as e:
                        print(f"❌ Ошибка отправки пользователю {chat_id}: {e}")
                
                conn.commit()
                conn.close()
                time.sleep(5)  # Проверяем каждые 5 секунд
            except Exception as e:
                print(f"Ошибка в потоке: {e}")
                time.sleep(5)
    
    thread = threading.Thread(target=check_loop, daemon=True)
    thread.start()

# ===================================================
# ЗАПУСК БОТА
# ===================================================

def start_message_checker(app):
    """Запускает проверку сообщений в отдельном потоке (простой способ)"""
    
    def check_loop():
        while True:
            try:
                conn = sqlite3.connect('exchange_bot.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, chat_id, text FROM messages_to_send WHERE sent = 0')
                messages = cursor.fetchall()
                
                for msg_id, chat_id, text in messages:
                    try:
                        # Самый простой способ: создать новый event loop для каждой отправки
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            app.bot.send_message(
                                chat_id=chat_id,
                                text=text,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=get_payment_keyboard()
                            )
                        )
                        cursor.execute('UPDATE messages_to_send SET sent = 1 WHERE id = ?', (msg_id,))
                        print(f"✅ Сообщение отправлено пользователю {chat_id}")
                    except Exception as e:
                        print(f"❌ Ошибка отправки: {e}")
                        cursor.execute('DELETE FROM messages_to_send WHERE id = ?', (msg_id,))
                
                conn.commit()
                conn.close()
                time.sleep(5)
            except Exception as e:
                print(f"Ошибка в потоке: {e}")
                time.sleep(5)
    
    thread = threading.Thread(target=check_loop, daemon=True)
    thread.start()

def main():
    init_db()
    
    TOKEN = 'your_token'
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    start_message_checker(application)
    start_rate_updater()
    
    print('🤖 Бот запущен! Клавиатура появится внизу экрана.')
    print('Нажмите Ctrl+C для остановки')

    application.run_polling()

if __name__ == '__main__':
    main()