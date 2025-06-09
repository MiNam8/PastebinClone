# Name of your virtual environment directory
VENV ?= venv

.PHONY: help install run test clean lint

help:
	@echo "Common commands:"
	@echo "  make install   - Install dependencies with Poetry"
	@echo "  make run       - Run the FastAPI app"
	@echo "  make run-docker - Run for Docker (no reload)"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linting"
	@echo "  make clean     - Clean up"

venv:
	python3 -m venv $(VENV)

install:
	poetry install

run:
	poetry run uvicorn app.main:app --reload

run-docker:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	poetry run pytest

lint:
	poetry run black .
	poetry run isort .
	poetry run flake8 .

clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Migration commands
migrate:
	poetry run alembic upgrade head

migrate-create:
	poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	poetry run alembic downgrade -1