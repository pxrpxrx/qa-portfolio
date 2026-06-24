Руководство по тестированию PostgreSQL через DBeaver

Проект: Crypto Arbitrage Bot
Инструмент: DBeaver 23.0+
База данных: PostgreSQL 16.0
Автор: Константин Горбунов (QA Engineer)

1. Подключение к базе данных

1. Открыть DBeaver
2. Нажать New Connection → выбрать PostgreSQL
3. Заполнить поля:
   Host: IP-адрес сервера
   Port: 5432
   Database: arbitrage_db
   Username: postgres
   Password: ******
4. Нажать Test Connection → Finish

2. Основные таблицы

Таблица button_set (настройки пользователей)

CREATE TABLE button_set (
    chat_id BIGINT PRIMARY KEY,
    awaiting_field INTEGER DEFAULT 0,
    selected_exchanges TEXT,
    spread_threshold DECIMAL(5,2),
    budget DECIMAL(15,2),
    telegram_username VARCHAR(50)
);

chat_id - ID пользователя в Telegram
awaiting_field - шаг ожидания ввода (0-9)
selected_exchanges - список выбранных бирж
spread_threshold - порог спреда в %
budget - бюджет пользователя

Таблица coin_data (данные о сетях)

CREATE TABLE coin_data (
    id SERIAL PRIMARY KEY,
    coin_name VARCHAR(50),
    chain_type VARCHAR(50),
    withdraw_fee DECIMAL(15,8),
    confirmation INTEGER,
    chain VARCHAR(50),
    exchange VARCHAR(50),
    contract_address VARCHAR(100)
);

coin_name - название монеты
chain_type - тип сети
withdraw_fee - комиссия за вывод
confirmation - количество подтверждений
exchange - название биржи

3. SQL-запросы для тестирования

3.1 Проверка настроек пользователя

SELECT chat_id, awaiting_field, spread_threshold 
FROM button_set 
WHERE chat_id = 123456789;

Ожидаемый результат: все поля заполнены корректно

3.2 Проверка выбранных бирж

SELECT selected_exchanges 
FROM button_set 
WHERE chat_id = 123456789;

Ожидаемый результат: строка с биржами

3.3 Проверка данных о сетях

SELECT coin_name, chain_type, withdraw_fee, exchange
FROM coin_data
WHERE coin_name = 'USDT'
ORDER BY exchange;

Ожидаемый результат: для каждой биржи указана комиссия

3.4 Проверка на дубликаты

SELECT chat_id, COUNT(*)
FROM button_set
GROUP BY chat_id
HAVING COUNT(*) > 1;

Ожидаемый результат: пустой результат

3.5 Проверка на NULL-значения

SELECT COUNT(*)
FROM coin_data
WHERE withdraw_fee IS NULL;

Ожидаемый результат: 0

3.6 Проверка всех бирж

SELECT DISTINCT exchange
FROM coin_data
ORDER BY exchange;

Ожидаемый результат: MEXC, Bybit, HTX, Gate, Bitget, OKX

3.7 Проверка на отрицательные комиссии

SELECT coin_name, exchange, withdraw_fee
FROM coin_data
WHERE withdraw_fee < 0;

Ожидаемый результат: пустой результат

4. Чек-лист тестирования БД

1. Подключение к БД успешно
2. Настройки пользователя сохраняются
3. Нет дублей пользователей
4. Нет NULL-значений в coin_data
5. Все биржи присутствуют
6. Нет отрицательных комиссий

5. Типичные проблемы

Не удается подключиться - проверить хост/порт/пароль
Данные не обновляются - проверить воркфлоу Network Updater
Неверная комиссия - проверить API биржи

6. Используемые инструменты

DBeaver
DataGrip
PostgreSQL CLI

Автор: Константин Горбунов
Дата: 2025-06-21