run:
	streamlit run app/run_app.py

test:
	PYTHONPATH=./ python tests/test_connection.py

format:
	black . --line-length 100

lint:
	flake8 . --ignore=E501

streamlit:
	streamlit run app/run_app.py

# 🔄 Запуск усього проєкту (формат, лінт, тести, Streamlit)
project: format lint unittest
	streamlit run app/app.py

# ☁️ Build & deploy на GCP
build:
	gcloud builds submit --tag gcr.io/autoreportbot/auto-report .

deploy:
	gcloud run deploy auto-report \
		--image gcr.io/autoreportbot/auto-report \
		--platform managed \
		--region europe-west1 \
		--allow-unauthenticated

# 🧪 Юніт-тести з правильним шляхом
unittest:
	PYTHONPATH=./ pytest tests/

# 🔁 Збірка і деплой
all: build deploy
