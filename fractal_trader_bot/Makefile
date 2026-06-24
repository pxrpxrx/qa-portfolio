.PHONY: test test-cov lint clean

# Запуск всех тестов
test:
	pytest tests/ -v

# Запуск тестов с coverage
test-cov:
	pytest tests/ -v --cov=src --cov-report=term --cov-report=html

# Линтинг (flake8)
lint:
	flake8 src/ tests/ --max-line-length=100

# Очистка кэша и временных файлов
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "*.log" -delete
	rm -f daily_stats.json
