# ATR Trailing Stop Bot — BingX

Автоматизированный торговый бот для криптовалютной биржи **BingX**. Основная стратегия — трейлинг стоп-лосс на основе ATR с возможностью переключения на фрактальные стопы в ручном режиме при достижении безубытка.

---

## Возможности

- **ATR Trailing Stop** — автоматический пересчёт стоп-лосса при движении цены
- **Фрактальные стопы** — в ручном режиме стоп обновляется по фрактальным уровням
- **Безубыток (Breakeven)** — при достижении +0.2% PnL стоп подтягивается к цене входа
- **BTC-корреляция** — если срабатывает стоп по BTC, автоматически закрываются все альт-позиции
- **Мониторинг PnL** — процентный контроль позиций с решениями на Stop Loss / Take Profit
- **Риск-менеджмент** — дневные лимиты убытков, чёрный список, торговые часы, аварийная остановка

---

## Технологический стек

| Компонент | Технология |
|:---|:---|
| Язык | Python 3.10+ |
| Биржа | BingX (тестнет / реальная) |
| API | HMAC-SHA256 signed requests |
| Расчёты | ATR (14 period), фракталы (Williams) |
| Тестирование | pytest, pytest-cov, mock |
| Зависимости | requests, pandas, numpy, ccxt |

---

## Архитектура

```
src/
├── bx_trail_traider.py      # Главный модуль: ATRTrailingMonitor
├── services/
│   ├── bx_monitor.py        # BxMonitor — PnL-мониторинг позиций
│   ├── bx_trader.py         # BingXTrader — полный цикл ордеров
│   └── bx_risk_manager.py   # RiskManager — риск-лимиты
└── utilities/
    ├── bx_api.py            # BingXAPI — HMAC-подписанный клиент
    ├── bx_atr.py            # ATR — расчёт волатильности
    ├── config_loader.py     # ConfigLoader — загрузка JSON конфига
    └── klineData.py         # BingXKlineData — свечные данные
```

### Основные классы

- **ATRTrailingMonitor** — циклический мониторинг (25с), обновление ATR-стопов, переключение в ручной режим при безубытке
- **BxMonitor** — процентный контроль позиций, решения Stop Loss / Take Profit, rate limiting
- **BingXTrader** — открытие/закрытие позиций, стопы/тейки, проверка плеча, отмена ордеров
- **RiskManager** — чёрный/белый список, дневной лимит убытков, просадка, торговые часы
- **BingXAPI** — HMAC-SHA256 подпись, запросы к BingX, кэш минимальных количеств

---

## Установка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd trader_assistant_bot

# Установить зависимости
pip install -r src/requirements.txt

# Настроить конфиг
cp src/utilities/config/config.json.template src/utilities/config/config.json
# Отредактировать config.json: вставить API_KEY, API_SECRET
```

---

## Конфигурация

`src/utilities/config/config.json`:
```json
{
  "bingx": {
    "api_key": "YOUR_API_KEY_HERE",
    "api_secret": "YOUR_API_SECRET_HERE",
    "testnet": true
  },
  "scan": { "interval_seconds": 900 },
  "monitor": { "interval_seconds": 5 },
  "trading": { "capital_per_trade": 100 },
  "modes": { "emergency_stop": false }
}
```

`risk_config.json`:
```json
{
  "max_positions": 25,
  "max_position_size_abs": 25,
  "min_position_size": 5.0,
  "daily_loss_limit_abs": 10,
  "max_drawdown_percent": 15.0,
  "blacklist": [],
  "whitelist": [],
  "trading_hours": { "start": 0, "end": 24 },
  "weekend_trading": true,
  "emergency_stop": false
}
```

---

## Запуск

```bash
# ATR Trailing Monitor
python src/bx_trail_traider.py

# PnL Monitor
python src/services/bx_monitor.py
```

---

## Тестирование

```bash
cd tests
pip install -r requirements-test.txt
pytest -v
```

---

## Известные проблемы

- `bx_fractal.py` и `positionSizing.py` отсутствуют в репозитории (BUG-002)
- `ConfigLoader` падает при отсутствии `config.json` (BUG-001)
