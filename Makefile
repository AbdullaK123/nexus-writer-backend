.PHONY: start stop rebuild start-api stop-api rebuild-api start-db stop-db reset-db logs shell dbshell migrate upgrade

start:
	./dev_scripts/start_backend.sh

stop:
	./dev_scripts/stop_backend.sh

rebuild:
	./dev_scripts/rebuild_backend.sh

start-api:
	./dev_scripts/start_api.sh

stop-api:
	./dev_scripts/stop_api.sh

rebuild-api:
	./dev_scripts/rebuild_api.sh

start-db:
	./dev_scripts/start_db.sh

stop-db:
	./dev_scripts/stop_db.sh

reset-db:
	./dev_scripts/reset_db.sh

logs:
	docker compose logs -f $(or $(s),nexus-writer)

shell:
	./dev_scripts/shell.sh

dbshell:
	./dev_scripts/dbshell.sh

migrate:
	./dev_scripts/migrate.sh $(name)

upgrade:
	./dev_scripts/upgrade.sh