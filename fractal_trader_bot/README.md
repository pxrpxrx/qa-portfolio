# Fractal Trader Bot — автоматическая торговля на BingX по фракталам

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)
![BingX](https://img.shields.io/badge/BingX-API-0A66C2?style=flat)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Описание проекта

Fractal Trader Bot — автоматический торговый бот для BingX (USDT-M фьючерсы), использующий **фрактальный анализ Уильямса** для генерации сигналов.

### Как это работает

1. **Сбор данных** — получение свечных данных с BingX API для сканируемых монет
2. **Фрактальный анализ** — поиск паттернов «верхний/нижний фрактал» (5-свечные формации с экстремумом по центру)
3. **Классификация режима** — определение рыночного режима (TREND_UP, TREND_DOWN, RANGE, VOLATILE) через EMA200, ADX, ATR
4. **Сигналы** — комбинация фракталов, режима и дополнительных фильтров формирует точки входа
5. **Позиционирование** — ATR-based расчёт размера позиции с фиксированным риском 1% на сделку
6. **Риск-менеджмент** — дневной лимит убытка, максимальная просадка, чёрный список, проверка R/R, аварийная остановка
7. **Мониторинг** — отслеживание открытых позиций, автоматическое закрытие по стоп/тейк процентам
8. **Логирование** — все сделки записываются в SQLite (positions.db) для последующего анализа

---

## 🛠️ Технологический стек

| Компонент               | Технология                |
|:------------------------|:---------------------------|
| **Язык**                | Python 3.10+              |
| **Биржа**               | BingX (USDT-M фьючерсы)   |
| **API**                 | BingX REST API (v2/v3)    |
| **База данных**         | SQLite (positions.db)     |
| **Анализ графиков**     | Фракталы Уильямса (5 свечей) |
| **Индикаторы**          | ATR, ADX, EMA200          |
| **Управление рисками**  | ATR-based позиционирование |
| **Тестирование**        | pytest, unittest.mock     |

---

## 📂 Структура проекта

```
fractal_trader_bot/
├── README.md
├── LICENSE
├── .gitignore
├── Makefile
├── risk_config.json
├── src/
│   ├── bx_orchestrator.py          # Главный торговый цикл
│   ├── requirements.txt            # Зависимости
│   ├── utilities/
│   │   ├── bx_api.py               # BingX API клиент
│   │   ├── bx_atr.py               # Расчёт ATR
│   │   ├── bx_db_writer.py         # SQLite запись сделок
│   │   ├── bx_risk_manager.py      # Риск-менеджмент
│   │   ├── config_loader.py        # Загрузчик конфигурации
│   │   ├── config/config.json      # Файл конфигурации (шаблон)
│   │   ├── klineData.py            # Получение свечных данных
│   │   └── positionSizing.py       # Расчёт размера позиции
│   ├── trading_services/
│   │   ├── bx_fractal_finder.py    # Поиск фракталов
│   │   ├── bx_monitor.py           # Мониторинг позиций
│   │   ├── bx_order_editor.py      # Редактор ордеров
│   │   ├── bx_signal_parser.py     # Парсинг сигналов → ордера
│   │   ├── bx_trader.py            # Логика торговли
│   │   ├── regime_classifier.py    # Классификация режима
│   │   └── SIMULATOR.py            # Торговый симулятор
│   └── analyze_trades/
│       ├── analyzeTrades.py        # Анализ сделок
│       ├── bingx_history.py        # История BingX
│       ├── calibrateIndicators.py  # Калибровка индикаторов
│       └── viewTrades.py           # Просмотр сделок
├── tests/
│   ├── conftest.py                 # Pytest фикстуры
│   ├── pytest.ini                  # Конфигурация pytest
│   ├── requirements-test.txt       # Зависимости для тестов
│   ├── test_position_sizing.py     # Тесты positionSizing
│   ├── test_risk_manager.py        # Тесты RiskManager
│   ├── test_db_writer.py           # Тесты BingXDBWriter
│   ├── test_signal_parser.py       # Тесты BingXOrderPreparer
│   └── test_fractal_finder.py      # Тесты FractalFinder
└── docs/
    ├── test-plan.md                # Тест-план
    ├── test-cases/
    │   ├── TC-001.md               # Расчёт размера позиции
    │   ├── TC-002.md               # Глобальные риск-лимиты
    │   ├── TC-003.md               # Запись/обновление в БД
    │   ├── TC-004.md               # Поиск верхнего фрактала
    │   ├── TC-005.md               # Подготовка ордера LONG
    │   └── TC-006.md               # Минимальные стопы
    ├── bug-reports/
    │   └── BUG-001.md              # ConfigLoader FileNotFoundError
    └── checklists/
        └── regression-checklist.md # Регрессионный чек-лист
```

---

## 🚀 Установка и запуск

### Предварительные требования
- Python 3.10+
- Виртуальное окружение (рекомендуется)
- API-ключи BingX (основная или тестовая сеть)

### Установка

```bash
# Клонировать репозиторий
cd fractal_trader_bot

# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r src/requirements.txt
```

### Настройка

1. Скопируйте `src/utilities/config/config.json` и填入те свои API-ключи BingX
2. Отредактируйте `risk_config.json` под свои риск-параметры
3. По желанию: настройте список мониторинга в `bingx_symbols.json`

### Запуск

```bash
# Запуск оркестратора (основной режим)
python -m src.bx_orchestrator

# Запуск только мониторинга
python -m src.trading_services.bx_monitor

# Запуск редактора ордеров
python -m src.trading_services.bx_order_editor
```

---

## 🧪 Тестирование

Проект покрыт модульными тестами (pytest) с использованием `unittest.mock` для изоляции внешних зависимостей.

```bash
# Установка тестовых зависимостей
pip install -r tests/requirements-test.txt

# Запуск всех тестов
pytest tests/ -v

# Запуск с coverage
pytest tests/ -v --cov=src

# Запуск конкретного файла
pytest tests/test_position_sizing.py -v
```

### Структура тестов

| Файл                        | Что тестирует                     | Зависимости |
|:----------------------------|:----------------------------------|:------------|
| `test_position_sizing.py`   | positionSizing (расчёт размера)   | Нет         |
| `test_risk_manager.py`      | RiskManager (лимиты, чёрный список)| Нет         |
| `test_db_writer.py`         | BingXDBWriter (SQLite)            | Нет         |
| `test_signal_parser.py`     | BingXOrderPreparer (парсинг)      | Нет         |
| `test_fractal_finder.py`    | FractalFinder (фракталы)          | mock API    |

---

## 📊 Анализ сделок

После накопления истории сделок в `positions.db` можно запустить анализ:

```bash
python -m src.analyze_trades.analyzeTrades
python -m src.analyze_trades.viewTrades
```

---

## ⚙️ Конфигурация

### `config.json`
```json
{
  "bingx": {
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "testnet": true
  },
  "scan": { "interval_seconds": 900 },
  "monitor": { "interval_seconds": 5 },
  "trading": { "capital_per_trade": 100 },
  "modes": { "emergency_stop": false }
}
```

### `risk_config.json`
Настройки: `max_positions`, `daily_loss_limit_abs`, `max_drawdown_percent`, `blacklist`, `trading_hours`, `min_rr` и др.

---

## 📄 Лицензия

MIT License — подробнее в файле LICENSE.

---

## 📌 Статус проекта

Проект является учебным (pet-project). Вся документация, тест-кейсы и автотесты отражают реальный процесс тестирования и подход к обеспечению качества продукта.

**Автор:** Константин Горбунов  
**Роль:** QA Engineer, тестирование и документация  
**Год:** 2026
