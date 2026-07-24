.PHONY: run test lint migrate backup

run:
	python -m app.main

test:
	pytest -q --cov=app --cov-report=term-missing

lint:
	ruff check .
	mypy app

migrate:
	alembic upgrade head

backup:
	sqlite3 data/birthly.db ".backup data/backups/manual_$$(date +%Y%m%d_%H%M%S).db"
