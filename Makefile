PYTHON ?= python
HOST ?= 0.0.0.0
PORT ?= 8001

.PHONY: install run test lint typecheck check docker-build docker-up docker-down docker-logs

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT)

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy app

check: test lint typecheck

docker-build:
	docker build -t healthcare-compliance-ai:latest .

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f ai-service
