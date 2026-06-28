# Performance Tests — tbank_qrcode_service

Нагрузочные тесты на **k6 v2.0.0** для микросервиса платежей T-Bank QR.

## Тесты

| Файл | Тип | Описание | Когда использовать |
|------|-----|----------|-------------------|
| `load-test.js` | Load Test | Ramp-up до 50 VU, 3 эндпоинта, custom metrics | Базовая проверка производительности |
| `spike-test.js` | Spike Test | Резкий скачок до 200 VU за 5 секунд | Проверка устойчивости к всплескам |
| `stress-test.js` | Soak Test | 50 VU в течение 10 минут | Поиск утечек памяти, деградации |
| `negative-test.js` | Negative Test | Невалидные данные, SQL-инъекции, XSS | Проверка устойчивости к мусорным данным |

## Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/card/init` | Инициация карточного платежа |
| GET | `/api/sbp/init-and-qr` | Инициация СБП + получение QR |
| GET | `/api/qr/generate` | Генерация QR-кода (PNG) |
| POST | `/api/v1/manager/payment/init` | Init через менеджер (JSON body) |

## Запуск

```bash
# Предварительное условие: сервис запущен на localhost:8080
# Docker: docker-compose up -d
# Или mock-сервер для тестов: node mock-server.js

# Load test (базовый) — генерирует HTML-отчёт
k6 run load-test.js

# С кастомным URL и путём для отчёта
k6 run --env BASE_URL=http://localhost:9090 --env REPORT_DIR=./reports load-test.js

# Spike test
k6 run spike-test.js

# Soak test (10 минут!)
k6 run stress-test.js

# Negative test
k6 run negative-test.js
```

## HTML-отчёты

Load test автоматически генерирует HTML-отчёт в `reports/load-test-report.html`.

Отчёт содержит:
- Графики RPS и latency
- Таблицу thresholds (pass/fail)
- Custom metrics
- Summary с percentiles

Открой `reports/load-test-report.html` в браузере для просмотра.

## Thresholds (критерии успеха)

### Load Test
- `http_req_duration p(95) < 3000ms` — 95% запросов быстрее 3 секунд
- `http_req_duration p(99) < 5000ms` — 99% запросов быстрее 5 секунд
- `http_req_failed rate < 0.05` — менее 5% ошибок
- Custom: `payment_init_errors rate < 0.1`

### Spike Test
- `http_req_failed rate < 0.5` — до 50% ошибок допустимо при spike
- Цель: сервер не должен упасть (crash), допустимы 503

### Soak Test
- `http_req_failed rate < 0.1` — менее 10% ошибок за 10 минут
- `stress_errors rate < 0.15` — проверка деградации

### Negative Test
- `negative_unexpected_errors rate < 0.05` — сервер не должен падать от мусорных данных

## Custom Metrics

Load test собирает кастомные метрики:
- `payment_init_duration` — время инициации платежа
- `qr_generation_duration` — время генерации QR
- `card_init_duration` — время инициации карты
- `total_payments` — общее количество обработанных платежей
- `payment_init_errors` — ошибки инициации

## Интерпретация результатов

```
http_req_duration......: avg=1.2s  min=50ms  med=800ms  max=4.5s  p(95)=3.1s  p(99)=4.2s
                         ^^^ среднее  ^^^ медиана           ^^^ 95-й перцентиль
                         
http_req_failed........: 2.31% ✓ 1234  ✗ 29
                         ^^^ процент ошибок (должен быть < 5%)
```

**p(95) vs среднее:** Среднее чувствительно к выбросам. p(95) показывает, что 95% пользователей получили ответ быстрее этого значения — это реальнее отражает пользовательский опыт.
