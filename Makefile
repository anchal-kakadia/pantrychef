.PHONY: dev db-up db-down test lint

dev:           ## Start the API with hot reload
	uvicorn app.main:app --reload --port 8000

db-up:         ## Start Postgres + Redis
	docker compose up -d

db-down:       ## Stop and remove containers
	docker compose down

test:          ## Run all tests
	pytest tests/ -v

lint:          ## Lint and format
	ruff check app/ tests/ --fix