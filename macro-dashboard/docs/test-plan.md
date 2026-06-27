# План тестирования Macro Trading Dashboard

## 1. Объект тестирования

**Macro Trading Dashboard** — Java-приложение для макроэкономического анализа криптовалютного рынка.

**Репозиторий:** `qa-portfolio/macro-dashboard/`

## 2. Цели тестирования

- Проверить корректность математических вычислений (pctChange, mean, std, zScore)
- Проверить логику оценки макро-среды (GREEN/YELLOW/RED)
- Проверить оценку состояния BTC (BtcFrame)
- Проверить поиск дивергенций (DivergenceScanner)
- Проверить расчёты Gann Square of 9
- Проверить интеграцию всех компонентов (end-to-end)

## 3. Типы тестов

| Тип | Инструмент | Описание |
|-----|-----------|----------|
| Модульные (unit) | JUnit 5 + AssertJ | Тестирование утилит и бизнес-логики |
| Модульные (mock) | Mockito | Тестирование с моками зависимостей |
| Интеграционные | Spring Boot Test | End-to-end проверка пайплайна |
| Ручные | Postman / curl | Проверка HTML-вывода |

## 4. Инструменты

- **Java:** JUnit 5, AssertJ, Mockito
- **Allure:** отчёты о тестировании
- **Maven:** `mvn test` для запуска тестов
- **GitHub Actions:** CI/CD

## 5. Критерии качества

- **P0 (Критические):** 100% прохождение — математические утилиты, оценка макро-среды
- **P1 (Высокие):** 100% прохождение — BtcFrame, DivergenceScanner
- **P2 (Средние):** допустимы минимальные отклонения — Gann расчёты

## 6. Тестовые сценарии

| ID | Название | Приоритет |
|----|----------|-----------|
| TC-001 | pctChange: корректный расчёт изменения | P0 |
| TC-002 | mean/std/zScore: статистические функции | P0 |
| TC-003 | MacroContext: GREEN при бычьих сигналах | P0 |
| TC-004 | MacroContext: RED при медвежьих сигналах | P0 |
| TC-005 | BtcFrame: корректная оценка BTC | P1 |
| TC-006 | DivergenceScanner: поиск M2/BTC дивергенций | P1 |
| TC-007 | GannSquare9: price-to-angle расчёт | P2 |
| TC-008 | GannSquare9: support/resistance уровни | P2 |

## 7. Окружение

- **Java:** 17+
- **Maven:** 3.8+
- **Внешние зависимости:** FRED API, Yahoo Finance, Binance API (для интеграционных тестов)

## 8. Покрытие

- **DataManager:** 22 теста (pctChange, mean, std, zScore, priorValue)
- **MacroContext:** 7 тестов (GREEN/RED/YELLOW + факторы)
- **BtcFrame:** 9 тестов (сценарии + edge cases)
- **DivergenceScanner:** 7 тестов (DXY/BTC, M2/BTC)
- **GannSquare9:** 19 тестов (price-to-angle, S/R, форматирование)
- **Итого:** 64 теста
