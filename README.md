# QA Portfolio — Константин Горбунов

Привет. Я начинающий QA-инженер. В этом портфолио собрал примеры моей работы над 6 проектами — от Telegram-ботов до микросервисов.

## Проекты

| Проект | Суть | Что сделал |
|--------|------|-----------|
| [arbit_bot](./arbit_bot/) | Telegram-бот для мониторинга спредов криптобирж | Функциональное тестирование, API-тесты (JS), баг-репорты, Postman-коллекция |
| [exchanger_bot](./exchanger_bot/) | Telegram-бот криптообменника на Python/SQLite | Полный цикл: тест-план, кейсы, чеклисты, автотесты (pytest + Allure), DBeaver-схемы |
| [arbit_website](./arbit_website/) | Лендинг арбитражника (HTML/CSS) | Тест-кейсы, баг-репорты, UI-проверки, регрессионный чеклист |
| [fractal_trader_bot](./fractal_trader_bot/) | Торговый бот на фракталах (Python, BingX API) | 25 pytest-тестов, Allure, ruff + mypy, coverage, CI/CD, Postman |
| [trader_assistant_bot](./trader_assistant_bot/) | Трейлинг-стоп монитор (Python, WebSocket) | 132 pytest-теста, Allure, ruff + mypy, coverage, GitHub Actions |
| [tbank_qrcode_service](./tbank_qrcode_service/) | Микросервис приёма платежей (Java, Spring Boot) | JUnit 5 + MockMvc тесты, Docker Compose (PostgreSQL + Redis), Postman |

## Инструменты, доказанные в проектах

> Каждый инструмент подкреплён файлами в репозитории, тестами или CI-конфигами.

**Автоматизация:** pytest, JUnit 5 + MockMvc, Allure, ruff, mypy, pytest-cov  
**API:** Postman, Newman, REST, WebSocket, nock (JS mocking)  
**CI/CD:** GitHub Actions (lint → test → coverage)  
**Контейнеризация:** Docker, docker-compose (Java + PostgreSQL + Redis)  
**Нагрузка:** k6 (скрипт в `performance-tests/`)  
**БД:** SQLite, PostgreSQL, Redis, DBeaver, SQL  
**Окружение:** Git, Linux CLI, Nginx, Maven, VS Code, IntelliJ IDEA  
**Языки:** Python, Java, SQL, JavaScript (Node.js), HTML/CSS

## Инструменты — в процессе изучения

> Указаны в резюме, но пока без проектного следа в этом репозитории.
> Скриншоты / PDF-артефакты — следующий шаг.

| Куда добавить скриншот | Что показать |
|------------------------|-------------|
| `arbit_bot/docs/screenshots/` | Jira/Notion: пример баг-репорта с заполненными полями (Steps, Expected, Actual, Severity) |
| `exchanger_bot/docs/screenshots/` | TestRail / Qase: скриншот тест-рана с результатами |
| `fractal_trader_bot/docs/screenshots/` | Charles/Fiddler: перехваченный запрос к BingX API, тело и заголовки |
| `trader_assistant_bot/docs/screenshots/` | OWASP ZAP / Burp Suite: отчёт сканирования, найденные уязвимости |
| `tbank_qrcode_service/docs/screenshots/` | Grafana / Kibana: дашборд с метриками приложения (если есть доступ) |
| `performance-tests/screenshots/` | k6 / JMeter: отчёт нагрузочного теста, график RPS и latencies |

## Результаты

- **174+ Python-теста** проходят в 3 проектах
- **Java-тесты:** JUnit 5 + MockMvc (tbank_qrcode_service)
- **JS-тесты:** nock (arbit_bot)
- **2 Postman-коллекции** с реальных криптобирж (MEXC, Bybit, Bitget, OKX)
- **Docker Compose:** Java-микросервис + PostgreSQL + Redis
- **CI:** GitHub Actions на push/PR (ruff + pytest + coverage + maven)

## Контакты

- Email: pxrpxrx@gmail.com
- GitHub: [pxrpxrx](https://github.com/pxrpxrx)
- Роль: Junior QA Engineer
