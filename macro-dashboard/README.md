# Macro Trading Dashboard — мульти-горизонтный макро-анализ

Java-приложение для комплексного макроэкономического анализа криптовалютного рынка. Агрегирует данные из FRED (25 макро-серий), Yahoo Finance (30 тикеров) и Binance/CoinGecko, строит мульти-горизонтный анализ с системой GREEN/YELLOW/RED.

## Возможности

- **Макро-анализ:** ликвидность (M2, TGA, ON RRP), доходности (DGS, BAA, HYG), сектора (XLK, XLU, XLY), товары (GLD, Copper, Oil)
- **Мульти-горизонтный анализ:** 3 временных горизонта (1-2 недели, 1-3 месяца, 3-12 месяца) + 3 сценария с вероятностями
- **Микро-условия:** VIX, секторальная ротация, risk regime
- **Framework rows:** 21 парное соотношение активов (IMPULSE, WANT/MUST, TECH/UTILITIES и др.)
- **Дивергенции:** автоматический поиск расхождений между DXY/M2/BTC/HYG
- **Gann/астрология:** эфемериды планет, аспекты, Square of 9, лунные дни
- **HTML-дашборд:** визуальный отчёт с цветовой индикацией

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Язык | Java 17 (records, pattern matching) |
| Сборщик | Maven |
| Тесты | JUnit 5 + AssertJ + Mockito |
| Отчёты | Allure |
| CI/CD | GitHub Actions |
| Данные | FRED API, Yahoo Finance, Binance/CoinGecko |
| Вывод | ANSI-консоль + HTML дашборд |

## Архитектура

```
Data Layer (FRED, Yahoo, Binance)
    ↓
DataManager (Snapshot — 100+ полей)
    ↓
Analysis Layer (MacroContext, BtcFrame, DivergenceScanner)
    ↓
HorizonMatrix (3 горизонта + микро + сценарии)
    ↓
Output (Console ANSI / HTML Dashboard)
```

## Структура проекта

```
src/main/java/com/tradingtabs/
├── cli/           — Точки входа (Main, BacktestMain)
├── data/          — HTTP-клиенты (FredClient, CryptoClient)
├── engine/        — Анализ (DataManager, MacroContext, BtcFrame, DivergenceScanner)
├── gann/          — Gann/астрология (Ephemeris, AspectFinder, GannSquare9)
├── horizon/       — Мульти-горизонтный анализ (HorizonMatrix)
├── macro/         — Yahoo Finance клиент (MacroDataClient)
└── model/         — DTO (DashboardData, Prediction)

src/test/java/com/tradingtabs/
├── engine/        — Unit-тесты (DataManager, MacroContext, BtcFrame, DivergenceScanner)
└── gann/          — Unit-тесты (GannSquare9)
```

## Быстрый старт

```bash
# Сборка и запуск тестов
mvn clean test

# Запуск приложения
mvn clean package
java -jar target/macro-dashboard-1.0-SNAPSHOT.jar

# Или через run.bat (Windows)
run.bat
```

## Тестирование

### Модульные тесты (JUnit 5 + AssertJ + Mockito)

```bash
mvn test
```

64 теста покрывают:
- **DataManager** — утилиты `pctChange`, `mean`, `std`, `zScore`, `priorValue` (22 теста)
- **MacroContext** — GREEN/RED/YELLOW сценарии + факторы (7 тестов)
- **BtcFrame** — сценарии + edge cases + funding rate (9 тестов)
- **DivergenceScanner** — DXY/BTC и M2/BTC дивергенции (7 тестов)
- **GannSquare9** — price-to-angle, S/R уровни, форматирование (19 тестов)

### Allure отчёты

```bash
mvn allure:serve
```

## Источники данных

| Сервис | Что получает |
|--------|-------------|
| FRED API | ~25 макро-серий: M2SL, IORB, TGA, ON RRP, DGS10, BAA10Y, SOFR, PCE, дефицит, госдолг |
| Binance | BTC/USDT цена, funding rate, open interest |
| CoinGecko | 24h volume BTC, исторические цены |
| Yahoo Finance | ~30 тикеров: SPY, QQQ, GLD, TLT, HYG, XLK, XLU, XLY, XLP, XLF, NVDA, VIX, IWM |
