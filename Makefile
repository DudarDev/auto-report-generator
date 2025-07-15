# /Makefile

.PHONY: run test

# Запускає програму в ЛОКАЛЬНОМУ режимі
run:
    @echo "🚀 Запуск програми у ЛОКАЛЬНОМУ середовищі..."
    python -m streamlit run app

# Запускає тести в ТЕСТОВОМУ режимі
test:
	@echo "🧪 Запуск юніт-тестів у ТЕСТОВОМУ середовищі..."
	@export APP_ENV=test && PYTHONPATH=. venv/bin/pytest tests/