# Криптообменник — Telegram-бот для обмена BTC ↔ RUB

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![SQLite](https://img.shields.io/badge/SQLite-3-blue)
![License](https://img.shields.io/badge/License-MIT-green)

**Два Telegram-бота** (клиентский + админский) для обмена криптовалюты с интеграцией BestChange.

---

## 📌 Описание проекта

Проект состоит из двух ботов:
- **Клиентский бот** — для пользователей, которые хотят обменять BTC на RUB или RUB на BTC
- **Админский бот** — для операторов, которые обрабатывают заявки, подтверждают оплаты и управляют реквизитами

---

## 🛠️ Технологии

| Компонент | Технология |
|:---|:---|
| **Язык** | Python 3.10+ |
| **Фреймворк** | python-telegram-bot (PTB) 20.x |
| **База данных** | SQLite |
| **API курсов** | BestChange (приватное API) |
| **Дополнительно** | Bybit API, ЦБ РФ (курс USD/RUB) |

---

## 📂 Структура проекта
crypto-exchange-bot/
├── client_bot.py # Клиентский бот
├── admin_bot.py # Админский бот
├── exchange_bot.db # База данных SQLite
├── menu_commands # Сформированные кнопки для reply-keyboard Telegram
├── README.md
├── LICENSE
├── docs/
│ ├── test-plan.md
│ ├── regression-checklist.md
│ ├── database-schema.md
│ ├── api-documentation.md
│ ├── dbeaver-guide.md
│ ├── postman-collection.json
│ ├── postman-guide.md
│ ├── test-cases/
│ │ ├── TC-001.md
│ │ ├── TC-002.md
│ │ ├── TC-003.md
│ │ ├── TC-004.md
│ │ ├── TC-005.md
│ │ ├── TC-006.md
│ │ ├── TC-007.md
│ │ └── TC-008.md
│ └── bug-reports/
│ ├── BUG-001.md
│ ├── BUG-002.md
│ ├── BUG-003.md
│ └── BUG-004.md
└── tests/
├── test_api.py
├── test_database.py
├── test_bot_logic.py
├── conftest.py
├── pytest.ini
└── requirements-test.txt

---

## 🧩 Функционал

### Клиентский бот
- ✅ Главное меню (5 кнопок)
- ✅ Создание обмена (выбор валюты → ввод суммы → ввод реквизитов → подтверждение)
- ✅ Просмотр курсов и лимитов
- ✅ История заявок
- ✅ Поддержка
- ✅ Правила AML/KYC
- ✅ Загрузка чеков (PDF, фото)

### Админский бот
- ✅ Включение/выключение бота
- ✅ Просмотр заявок на подтверждение реквизитов (с пагинацией)
- ✅ Ввод реквизитов оператора
- ✅ Отправка реквизитов клиенту
- ✅ Просмотр заявок на подтверждение оплаты (с пагинацией)
- ✅ Подтверждение/отклонение оплаты

## 🧪 Автотесты

| Файл                  | Что тестирует                                     |
|:---                   |:---                                               |
| `test_api.py`         | BestChange API (позитивные и негативные сценарии) |
| `test_database.py`    | SQLite (CRUD операции, целостность данных)        |
| `test_bot_logic.py`   | Бизнес-логика (конвертация, создание заявок)      |

## 📸 Результаты API-тестирования (Allure)

В рамках тестирования интеграции с BestChange API были выполнены позитивные и негативные сценарии. Тесты запускались через Newman, а отчет сгенерирован в Allure.

![Общий отчет](assets/allure-overview.png)
*Общая статистика выполнения тестов.*
![Успешный сценарий](assets/allure-success-test.png)
*Пример позитивного теста с корректным API-ключом.*
![Обработка ошибки](assets/allure-error-test.png)
*Пример негативного теста: проверка ответа при неверном API-ключе.*

## 📸 Интерфейс ботов

![Главное меню клиента](assets/client-main-menu.png)
![Создание обмена](assets/client-create-exchange.png)
![Админ-панель](assets/admin-panel.png)

---

## 🚀 Запуск

### Установка зависимостей

pip install python-telegram-bot requests

### Настройка
- Получить токены ботов через @BotFather
- Получить API-ключ BestChange
- Вставить токены в client_bot.py и admin_bot.py

### Запуск клиентского бота
python client_bot.py

# Запуск админского бота (в отдельном терминале)
python admin_bot.py

### Основные таблицы:
users — пользователи и их состояния
orders — заявки на обмен
cached_rates — кэш курсов
messages_to_send — отложенные сообщения
Подробнее — в docs/database-schema.md

### Проект покрыт тестовой документацией и автотестами:
Тест-план	Стратегия тестирования
Чек-лист	   Регрессионные проверки
Тест-кейсы	8 сценариев (TC-001 — TC-008)
Баг-репорты	4 отчёта (BUG-001 — BUG-004)
Автотесты	API, БД, бизнес-логика (Pytest)
Postman	   Коллекция для BestChange API
DBeaver   	Инструкция по работе с БД

MIT License — подробнее в файле LICENSE.

Автор: Константин Горбунов
Роль: QA Engineer, тестирование и документация
Год: 2026