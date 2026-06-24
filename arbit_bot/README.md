# Crypto Arbitrage Bot — Telegram Assistant for Spread Monitoring

![n8n](https://img.shields.io/badge/n8n-0.238.0-blueviolet?style=flat&logo=n8n)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0-336791?style=flat&logo=postgresql)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat&logo=javascript)
![Linux](https://img.shields.io/badge/Ubuntu-22.04-E95420?style=flat&logo=ubuntu)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Описание проекта

Telegram-бот для автоматического мониторинга межбиржевых спредов криптовалют.

Пользователь через Telegram-интерфейс настраивает параметры:
- Выбор бирж (BingX, MEXC, Bybit, HTX, Gate, Bitget, OKX)
- Размер спреда (%)
- Комиссии
- Сети и токены
- Бюджет

Бот в реальном времени:
- Получает данные с публичных API бирж
- Рассчитывает спред между биржами
- Уведомляет пользователя при превышении порога
- Автоматически обновляет данные о сетях (ежесуточно)
- Интегрирован с платежным модулем

> Проект создан как pet-проект для изучения автоматизации и работы с API.

---

## 🛠️ Технологический стек

| Компонент | Технология |
|:---|:---|
| **Оркестрация** | n8n (workflow automation) |
| **Логика** | JavaScript (Code-ноды n8n) |
| **База данных** | PostgreSQL 16 (удаленный сервер) |
| **Сервер** | Ubuntu 22.04 (VPS) + Nginx |
| **API бирж** | BingX, MEXC, Bybit, HTX, Gate.io, Bitget, OKX |
| **Telegram** | Telegram Bot API (n8n-ноды) |
| **Безопасность** | Cloudflare (подпись запросов) |

---

## 📂 Структура проекта
arbitrage-bot/
├── README.md
├── LICENSE
├── .gitignore
├── n8n-workflows/
│ ├── telegram-front.json
│ └── spread-count.json
├── docs/
│ ├── test-plan.md
│ ├── regression-checklist.md
│ ├── api-documentation.md
│ ├── dbeaver-guide.md
│ ├── postman-collection.json
│ ├── postman-guide.md
│ ├── test-cases/
│ │ ├── TC-001.md
│ │ ├── TC-002.md
│ │ ├── TC-003.md
│ │ └── TC-004.md
│ └── bug-reports/
│ ├── BUG-001.md
│ ├── BUG-002.md
│ ├── BUG-003.md
│ └── BUG-004.md
└── tests/
├── test_spread_logic.js
├── test_api_basic.js
└── package.json

---

## 🧩 Функционал

### Telegram-интерфейс
- ✅ Настройка бирж
- ✅ Настройка порога спреда
- ✅ Настройка комиссий
- ✅ Настройка сетей и токенов
- ✅ Настройка бюджета
- ✅ Получение уведомлений о спреде

### Логика расчета спреда
- ✅ Сбор данных с 7+ криптобирж
- ✅ Расчет спреда в реальном времени
- ✅ Фильтрация спредов > 50% и отрицательных значений
- ✅ Автоматический расчет объема на основе стакана

### Инфраструктура
- ✅ PostgreSQL для хранения настроек пользователей
- ✅ Ежесуточное обновление данных о сетях
- ✅ Интеграция с платежным модулем
- ✅ Nginx для проксирования запросов

---

## 📸 Результаты тестирования

В рамках работы над проектом была разработана полная тестовая документация, включающая тест-план, чек-листы, тест-кейсы и баг-репорты. Проект является учебным (pet-project) и в данный момент не поддерживается, поэтому скриншоты выполнения тестов не приложены.
Однако вся документация и автотесты полностью отражают реальный процесс тестирования и подход к обеспечению качества продукта.

---

## 🚀 Развертывание

### Предварительные требования
- Ubuntu 22.04+ или локальная машина
- Node.js 18+ (для n8n)
- PostgreSQL 16+
- Nginx (опционально)

### Установка n8n
```bash
npm install n8n -g
n8n start
Или через Docker:

bash
docker run -d --restart unless-stopped \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
Настройка базы данных
sql
CREATE TABLE button_set (
    chat_id BIGINT PRIMARY KEY,
    awaiting_field INTEGER DEFAULT 0
);

CREATE TABLE coin_data (
    id SERIAL PRIMARY KEY,
    coin_name VARCHAR(50),
    chain_type VARCHAR(50),
    withdraw_fee DECIMAL,
    confirmation INTEGER,
    chain VARCHAR(50),
    exchange VARCHAR(50),
    contract_address VARCHAR(100)
);
Настройка Telegram Bot
Создать бота через @BotFather

Получить API-токен

Указать его в credentials n8n

## 📊 База данных

Основные таблицы:

button_set — настройки пользователей (биржи, спред, бюджет)
coin_data — данные о сетях и комиссиях
Подробнее — в docs/database-schema.md

## 🧪 Тестирование

Проект покрыт тестовой документацией и автотестами:

| Артефакт            | Описание                                     |
|:---                 |:---                                          |
| **Тест-план**       | Стратегия тестирования                       |
| **Чек-лист**        | Регрессионные проверки                       |
| **Тест-кейсы**      | 4 сценария (TC-001 — TC-004)                 |
| **Баг-репорты**     | 4 отчёта (BUG-001 — BUG-004)                 |
| **Автотесты**       | Логика расчета спреда, API бирж (JavaScript) |
| **Postman**         | Коллекция для API бирж                       |
| **DBeaver**         | Инструкция по работе с PostgreSQL            |

## 📄 Лицензия

MIT License — подробнее в файле LICENSE.

## 📌 Статус проекта

Проект является учебным (pet-project). На момент публикации портфолио инфраструктура не поддерживается, однако вся документация, тест-кейсы и автотесты полностью отражают реальный процесс тестирования и подход автора.

Автор: Константин Горбунов
Роль: QA Engineer, тестирование и документация
Год: 2026