.PHONY: help up down logs ps backend-shell backend-migrate backend-test backend-lint frontend-install frontend-test frontend-lint

help:
	@echo "Targets:"
	@echo "  up               Start full stack (docker compose)"
	@echo "  down             Stop stack"
	@echo "  logs             Tail logs"
	@echo "  ps               List containers"
	@echo "  backend-shell    Open backend shell"
	@echo "  backend-migrate  Run backend migrations"
	@echo "  backend-test     Run backend tests"
	@echo "  backend-lint     Run backend lint (ruff)"
	@echo "  frontend-install Install frontend deps (npm ci)"
	@echo "  frontend-test    Run frontend tests"
	@echo "  frontend-lint    Run frontend lint"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

backend-shell:
	docker compose exec backend bash

backend-migrate:
	docker compose exec backend python manage.py migrate

backend-test:
	docker compose exec backend pytest -q

backend-lint:
	docker compose exec backend ruff check .

frontend-install:
	cd frontend && npm ci

frontend-test:
	cd frontend && npm test -- --watch=false

frontend-lint:
	cd frontend && npm run lint

