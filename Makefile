# Makefile

run:
	python main.py

test:
	python test_connection.py

format:
	black . --line-length 100

lint:
	flake8 . --ignore=E501
