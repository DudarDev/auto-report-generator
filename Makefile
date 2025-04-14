run:
	python main.py

test:
	python test_connection.py

format:
	black . --line-length 100

lint:
	flake8 . --ignore=E501

streamlit:
	streamlit run app.py

# Запуск усього проєкту (формат, тест, Streamlit)
project: format lint test
	streamlit run app.py

# Build & deploy на GCP
build:
	gcloud builds submit --tag gcr.io/autoreportbot/auto-report .

deploy:
	gcloud run deploy auto-report \
		--image gcr.io/autoreportbot/auto-report \
		--platform managed \
		--region europe-west1 \
		--allow-unauthenticated

all: build deploy
