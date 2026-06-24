# QA Portfolio — Константин Горбунов

Портфолио с примерами работы по тестированию и обеспечению качества для 6 проектов.

## Состав портфолио

| Проект | Тип | Технологии | Автотесты | QA-документация |
|--------|-----|-----------|-----------|----------------|
| [arbit_bot](./arbit_bot/) | Telegram-бот мониторинга спредов | n8n, PostgreSQL, JS | JS (2 файла) | TC: 4, BR: 4, test-plan, checklist |
| [exchanger_bot](./exchanger_bot/) | Telegram-бот обменника | Python, SQLite, pytest | Python (3 файла) + Allure | TC: 8, BR: 4, test-plan, checklist |
| [arbit_website](./arbit_website/) | Лендинг для арбитражника | HTML, CSS | — | TC: 6, BR: 4, test-plan, checklist |
| [fractal_trader_bot](./fractal_trader_bot/) | Торговый бот (фракталы) | Python, BingX API | Python (6 файлов, 25 тестов) | TC: 6, BR: 1, test-plan, checklist |
| [trader_assistant_bot](./trader_assistant_bot/) | Трейлинг-стоп монитор | Python, BingX API, WS | Python (5 файлов, 132 теста) | TC: 4, BR: 2, test-plan, checklist |
| [tbank_qrcode_service](./tbank_qrcode_service/) | Микросервис приёма платежей | Java 17, Spring Boot 3 | Python + Java (22 теста) | TC: 4, BR: 2, test-plan, checklist |

## Что входит в каждый проект

- **README** — описание, архитектура, стек, инструкция по запуску
- **docs/test-plan.md** — стратегия тестирования
- **docs/test-cases/** — тест-кейсы (функциональные, негативные, граничные)
- **docs/bug-reports/** — баг-репорты с приоритетами
- **docs/checklists/regression-checklist.md** — регрессионный чек-лист
- **docs/postman/** — Postman-коллекции для API-тестирования
- **Автотесты** — pytest / JUnit 5 / JavaScript
- **CI/CD** — GitHub Actions для автоматического прогона тестов
- **Dockerfile** — контейнеризация

## Инструменты

- Python 3.14, pytest, pytest-mock, allure-pytest
- Java 17, JUnit 5, MockMvc, Mockito
- JavaScript, Node.js
- Maven, pip
- Docker, docker-compose
- GitHub Actions
- Postman / Newman
- DBeaver (PostgreSQL, SQLite)
- ruff (линтер)

## Результаты тестирования

Подробный отчёт: [tests-results/GLOBAL-TEST-REPORT.md](./tests-results/GLOBAL-TEST-REPORT.md)

| Проект | Тесты | Статус |
|--------|-------|--------|
| exchanger_bot | 17 pytest | ✅ 17/17 |
| fractal_trader_bot | 25 pytest | ✅ 25/25 |
| trader_assistant_bot | 132 pytest | ✅ 132/132 |
| arbit_bot | 8 JS | ⚠️ 4/8 (pre-existing issues) |

## Контакты

- **Автор:** Константин Горбунов
- **Email:** pxrpxrx@gmail.com
- **Роль:** QA Engineer
- **Год:** 2026
