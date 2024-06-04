run_build:
	docker compose -d --build

run:
	docker compose up -d

logs:
	docker compose logs

down:
	docker compose down
