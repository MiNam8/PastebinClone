# Name of your virtual environment directory
VENV ?= venv

.PHONY: help venv install run clean

help:
	@echo "Common commands:"
	@echo "  make venv      - Create a virtual environment"
	@echo "  make install   - Install dependencies"
	@echo "  make run       - Run the FastAPI app"
	@echo "  make clean     - Remove virtual environment"

venv:
	python3 -m venv $(VENV)

install: venv
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

run:
	. $(VENV)/bin/activate && uvicorn app.main:app --reload

clean:
	rm -rf $(VENV)