.PHONY: up down build logs ps migrate shell-backend shell-worker

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f backend worker

ps:
	docker compose ps

migrate:
	docker compose exec backend alembic upgrade head

shell-backend:
	docker compose exec backend /bin/sh

shell-worker:
	docker compose exec worker /bin/sh
