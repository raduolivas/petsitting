.PHONY: install run migrate seed test docker-up docker-down lint

install:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

run:
	. venv/bin/activate && python run.py

migrate:
	. venv/bin/activate && flask --app run:app db upgrade

seed:
	. venv/bin/activate && flask --app run:app seed

test:
	. venv/bin/activate && FLASK_ENV=testing SECRET_KEY=test pytest

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

lint:
	. venv/bin/activate && python -m compileall app run.py wsgi.py
