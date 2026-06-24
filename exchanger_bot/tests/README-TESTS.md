# Автотесты для Криптообменника

## Установка зависимостей
```bash
pip install -r requirements-test.txt

# Все тесты
pytest tests/

# Только API-тесты
pytest tests/test_api.py

# Только тесты БД
pytest tests/test_database.py

# С отчетом Allure
pytest tests/ --alluredir=allure-results
allure serve allure-results