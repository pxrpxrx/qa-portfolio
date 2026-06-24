Руководство по тестированию SQLite через DBeaver

Проект: Криптообменник
Инструмент: DBeaver 23.0+
База данных: SQLite
Файл: exchange_bot.db
Автор: Константин Горбунов (QA Engineer)

1. Подключение к базе данных

1. Открыть DBeaver
2. Нажать New Connection → выбрать SQLite
3. Нажать Next → Browse → выбрать exchange_bot.db
4. Нажать Finish

2. Основные таблицы

Таблица users (пользователи)

CREATE TABLE users (
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
);

chat_id - ID пользователя в Telegram
state - текущее состояние (main, awaiting_amount, awaiting_card_number и т.д.)
buy_currency - выбранная валюта покупки
sell_currency - выбранная валюта продажи
current_order_id - ID текущей заявки
client_card_number - номер карты клиента
client_phone_number - телефон клиента
client_bank_name - банк клиента
client_full_name - ФИО клиента
first_name - имя пользователя
username - username в Telegram

Таблица orders (заявки)

CREATE TABLE orders (
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
    client_card_number TEXT,
    client_phone_number TEXT,
    client_bank_name TEXT,
    client_full_name TEXT,
    operator_card_number TEXT,
    operator_bank_name TEXT,
    operator_full_name TEXT,
    operator_rub_amount REAL,
    operator_wallet_address TEXT,
    operator_network TEXT,
    operator_crypto_amount REAL,
    payment_detail_id INTEGER
);

order_id - ID заявки
chat_id - ID пользователя
order_number - номер заявки (ORD240515000001)
buy_currency - валюта покупки
sell_currency - валюта продажи
amount_rub - сумма в рублях
amount_btc - сумма в BTC
status - статус заявки (pending, pending_operator, awaiting_payment, awaiting_confirmation, pending_verification, completed, rejected, cancelled)
created_at - дата создания
paid_at - дата оплаты
tx_hash - хэш транзакции
receipt_file_id - ID файла чека
client_card_number - карта клиента
client_phone_number - телефон клиента
client_bank_name - банк клиента
client_full_name - ФИО клиента
operator_card_number - карта оператора
operator_bank_name - банк оператора
operator_full_name - ФИО оператора
operator_rub_amount - сумма для оплаты в рублях
operator_wallet_address - адрес кошелька
operator_network - сеть транзакции
operator_crypto_amount - сумма в криптовалюте

Таблица cached_rates (кэш курсов)

CREATE TABLE cached_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency_from TEXT,
    currency_to TEXT,
    rate REAL,
    reserve REAL,
    min_amount REAL,
    max_amount REAL,
    exchanger_id INTEGER,
    updated_at TEXT
);

currency_from - исходная валюта
currency_to - целевая валюта
rate - курс
reserve - резерв
min_amount - минимальная сумма
max_amount - максимальная сумма
exchanger_id - ID обменника
updated_at - время обновления

Таблица messages_to_send (отложенные сообщения)

CREATE TABLE messages_to_send (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    text TEXT,
    reply_markup TEXT,
    created_at TEXT,
    sent INTEGER DEFAULT 0
);

chat_id - ID получателя
text - текст сообщения
reply_markup - клавиатура (JSON)
created_at - время создания
sent - 0 (не отправлено) или 1 (отправлено)

3. SQL-запросы для тестирования

3.1 Проверка пользователя

SELECT chat_id, first_name, username, state 
FROM users 
WHERE chat_id = 123456789;

Ожидаемый результат: запись с данными пользователя

3.2 Проверка заявок пользователя

SELECT order_number, status, amount_rub, amount_btc, created_at
FROM orders
WHERE chat_id = 123456789
ORDER BY created_at DESC;

Ожидаемый результат: список заявок пользователя

3.3 Проверка активных заявок

SELECT order_number, status, amount_rub, amount_btc, created_at
FROM orders
WHERE status IN ('pending_operator', 'awaiting_payment', 'awaiting_confirmation', 'pending_verification')
ORDER BY created_at DESC;

Ожидаемый результат: список активных заявок

3.4 Проверка на дубликаты пользователей

SELECT chat_id, COUNT(*)
FROM users
GROUP BY chat_id
HAVING COUNT(*) > 1;

Ожидаемый результат: пустой результат

3.5 Проверка на NULL-значения в заявках

SELECT COUNT(*)
FROM orders
WHERE amount_rub IS NULL OR amount_btc IS NULL OR status IS NULL;

Ожидаемый результат: 0

3.6 Проверка на отрицательные суммы

SELECT order_number, amount_rub, amount_btc
FROM orders
WHERE amount_rub < 0 OR amount_btc < 0;

Ожидаемый результат: пустой результат

3.7 Проверка кэша курсов

SELECT currency_from, currency_to, rate, updated_at
FROM cached_rates
ORDER BY updated_at DESC
LIMIT 5;

Ожидаемый результат: актуальные курсы

3.8 Количество заявок по статусам

SELECT status, COUNT(*) as count
FROM orders
GROUP BY status;

Ожидаемый результат: статистика по статусам

4. Чек-лист тестирования БД

1. Подключение к БД успешно
2. Таблица users существует
3. Таблица orders существует
4. Таблица cached_rates существует
5. Нет дублей пользователей
6. Нет NULL-значений в amount_rub и amount_btc
7. Нет отрицательных сумм
8. Курсы обновляются в cached_rates

5. Типичные проблемы

Не удается подключиться - проверить путь к exchange_bot.db
Ошибка "table not found" - запустить бота для создания таблиц
Данные не сохраняются - проверить права на запись в папку с БД
Дубликаты пользователей - удалить дубли через SQL-запрос

6. Используемые инструменты

DBeaver
DataGrip
SQLite CLI

Автор: Константин Горбунов
Дата: 2026-06-21