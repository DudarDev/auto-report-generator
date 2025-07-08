# /Makefile

.PHONY: run test

# Запускає програму в ЛОКАЛЬНОМУ режимі
run:
	@echo "🚀 Запуск програми у ЛОКАЛЬНОМУ середовищі..."
	@export APP_ENV=local && PYTHONPATH=. venv/bin/streamlit run app/run_app.py

# Запускає тести в ТЕСТОВОМУ режимі
test:
	@echo "🧪 Запуск юніт-тестів у ТЕСТОВОМУ середовищі..."
	@export APP_ENV=test && PYTHONPATH=. venv/bin/pytest tests/