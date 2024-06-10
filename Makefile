run_build:
	docker compose up -d --build

run:
	docker compose up -d

logs:
	docker compose logs

down:
	docker compose down

superset_init:
	sudo docker exec -it hack_superset pip install psycopg2-binary prophet
	sudo docker exec -it hack_superset superset fab create-admin \
               --username admin \
               --firstname Superset \
               --lastname Admin \
               --email admin@admin.com \
               --password 12345; \
	sudo docker exec -it hack_superset superset db upgrade; \
	sudo docker exec -it hack_superset superset init;
	