# Схема базы данных: Криптообменник

**База данных:** SQLite  
**Файл:** `exchange_bot.db`

---

## Таблица `users` — пользователи

| Поле | Тип | Описание |
|:---|:---|:---|
| `chat_id` | INTEGER PRIMARY KEY | ID пользователя в Telegram |
| `state` | TEXT | Текущее состояние (main, awaiting_amount, и т.д.) |
| `buy_currency` | TEXT | Выбранная валюта покупки |
| `sell_currency` | TEXT | Выбранная валюта продажи |
| `current_order_id` | INTEGER | ID текущей заявки |
| `client_card_number` | TEXT | Номер карты клиента |
| `client_phone_number` | TEXT | Телефон клиента |
| `client_bank_name` | TEXT | Банк клиента |
| `client_full_name` | TEXT | ФИО клиента |
| `first_name` | TEXT | Имя пользователя |
| `username` | TEXT | Username в Telegram |

---

## Таблица `orders` — заявки на обмен

| Поле | Тип | Описание |
|:---|:---|:---|
| `order_id` | INTEGER PRIMARY KEY | ID заявки |
| `chat_id` | INTEGER | ID пользователя |
| `order_number` | TEXT | Номер заявки (ORD240515000001) |
| `buy_currency` | TEXT | Валюта покупки |
| `sell_currency` | TEXT | Валюта продажи |
| `amount_rub` | REAL | Сумма в рублях |
| `amount_btc` | REAL | Сумма в BTC |
| `status` | TEXT | Статус заявки |
| `created_at` | TEXT | Дата создания |
| `paid_at` | TEXT | Дата оплаты |
| `tx_hash` | TEXT | Хэш транзакции |
| `receipt_file_id` | TEXT | ID файла чека |
| `client_card_number` | TEXT | Карта клиента |
| `client_phone_number` | TEXT | Телефон клиента |
| `client_bank_name` | TEXT | Банк клиента |
| `client_full_name` | TEXT | ФИО клиента |
| `operator_card_number` | TEXT | Карта оператора |
| `operator_bank_name` | TEXT | Банк оператора |
| `operator_full_name` | TEXT | ФИО оператора |
| `operator_rub_amount` | REAL | Сумма для оплаты |
| `operator_wallet_address` | TEXT | Адрес кошелька |
| `operator_network` | TEXT | Сеть транзакции |
| `operator_crypto_amount` | REAL | Сумма в криптовалюте |
| `payment_detail_id` | INTEGER | ID реквизита |

---

## Таблица `cached_rates` — кэш курсов

| Поле | Тип | Описание |
|:---|:---|:---|
| `id` | INTEGER PRIMARY KEY | ID записи |
| `currency_from` | TEXT | Исходная валюта |
| `currency_to` | TEXT | Целевая валюта |
| `rate` | REAL | Курс |
| `reserve` | REAL | Резерв |
| `min_amount` | REAL | Минимальная сумма |
| `max_amount` | REAL | Максимальная сумма |
| `exchanger_id` | INTEGER | ID обменника |
| `updated_at` | TEXT | Время обновления |

---

## Таблица `messages_to_send` — отложенные сообщения

| Поле | Тип | Описание |
|:---|:---|:---|
| `id` | INTEGER PRIMARY KEY | ID сообщения |
| `chat_id` | INTEGER | ID получателя |
| `text` | TEXT | Текст сообщения |
| `reply_markup` | TEXT | Клавиатура (JSON) |
| `created_at` | TEXT | Время создания |
| `sent` | INTEGER | 0 — не отправлено, 1 — отправлено |

---

## Статусы заявок

| Статус | Описание |
|:---|:---|
| `pending` | Создана, ожидает данных клиента |
| `pending_operator` | Ожидает ввода реквизитов оператором |
| `awaiting_payment` | Ожидает оплаты от клиента |
| `awaiting_confirmation` | Клиент нажал "Оплачено", ожидает чек |
| `pending_verification` | Чек загружен, ожидает подтверждения |
| `completed` | Заявка выполнена |
| `rejected` | Заявка отклонена |
| `cancelled` | Заявка отменена |