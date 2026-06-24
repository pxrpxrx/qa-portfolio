# Global Test Results Report

**Date:** 2026-06-24
**Environment:** Windows, Python 3.14.6, Java 25 (Temurin), Node.js 24.17.0

## Summary

| Project | Language | Tests | Passed | Failed | Coverage |
|---------|----------|-------|--------|--------|---------|
| exchanger_bot | Python (pytest) | 17 | 17 | 0 | Unit + Integration |
| fractal_trader_bot | Python (pytest) | 25 | 25 | 0 | Unit (mocked API) |
| trader_assistant_bot | Python (pytest) | 132 | 132 | 0 | Unit (mocked API) |
| arbit_bot | JavaScript | 5+3 | 2+2 | 3+1 | API integration* |
| tbank_qrcode_service | Java (JUnit) | 7 | — | — | Needs source JAR |

\* arbit_bot tests fail due to network-dependent assertions and pre-existing test logic issues.

## Test Results by Project

### exchanger_bot — 17/17 PASSED
- `test_api.py` — 5 tests (API endpoints, response parsing)
- `test_bot_logic.py` — 7 tests (bot commands, menu, state machine)
- `test_database.py` — 5 tests (SQLite CRUD, schema validation)

### fractal_trader_bot — 25/25 PASSED
- `test_position_sizing.py` — 6 tests (position calc, stop/take, R/R)
- `test_risk_manager.py` — 6 tests (stop, blacklist, hours, limits)
- `test_fractal_finder.py` — 5 tests (fractal detection, nearest fractal)
- `test_signal_parser.py` — 4 tests (order prep, stop/take creation)
- `test_db_writer.py` — 4 tests (SQLite CRUD, stats)

### trader_assistant_bot — 132/132 PASSED
- `test_atr_calculation.py` — 9 tests (ATR calc, price, position)
- `test_kline_data.py` — 29 tests (klines, symbols, parsing, request)
- `test_monitor.py` — 26 tests (positions, sync, exits, rate limit)
- `test_risk_manager.py` — 48 tests (emergency, limits, blacklist, hours, size, price, drawdown, config)
- `test_trader.py` — 20 tests (open/close, balance, positions, stops, leverage)
