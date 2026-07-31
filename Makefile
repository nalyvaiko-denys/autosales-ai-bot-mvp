.PHONY: install lint test check up down migrate seed

install:
	python -m pip install -e '.[dev]'

lint:
	ruff check .
	ruff format --check .

test:
	pytest -q

check: lint test

up:
	docker compose up --build -d

down:
	docker compose down

migrate:
	docker compose run --rm migrate

seed:
	docker compose exec api python -m scripts.seed

