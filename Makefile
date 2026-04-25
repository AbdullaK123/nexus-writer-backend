.DEFAULT_GOAL := help

# ──────────────────────────────────────────────
# Colors
# ──────────────────────────────────────────────
CYAN   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
RED    := \033[31m
BOLD   := \033[1m
RESET  := \033[0m

# ──────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────
.PHONY: help
help: ## Show this help message
	@printf "\n$(BOLD)$(CYAN)Nexus Writer Backend$(RESET)\n"
	@printf "$(CYAN)════════════════════════════════════════$(RESET)\n\n"
	@awk 'BEGIN {FS = ":.*##"} \
		/^[a-zA-Z_-]+:.*##/ { printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2 } \
		/^## ---/ { printf "\n$(BOLD)$(YELLOW)%s$(RESET)\n", substr($$0, 8) }' $(MAKEFILE_LIST)
	@printf "\n"

## --- Stack
.PHONY: start stop rebuild restart status ps

start: ## Start entire backend (build + follow logs)
	./dev_scripts/start_backend.sh

stop: ## Stop entire backend (removes volumes)
	./dev_scripts/stop_backend.sh

rebuild: ## Full rebuild of all containers
	./dev_scripts/rebuild_backend.sh

restart: ## Restart API container without rebuilding
	docker compose restart nexus-writer && docker compose logs nexus-writer -f

status: ## Show container status and health
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

ps: ## Show all running containers (compact)
	@docker compose ps

## --- API
.PHONY: start-api stop-api rebuild-api health routes

start-api: ## Start only the API container
	./dev_scripts/start_api.sh

stop-api: ## Stop only the API container
	docker compose down nexus-writer

rebuild-api: ## Rebuild and restart the API container
	./dev_scripts/rebuild_api.sh

health: ## Check API health endpoint
	@curl -sf http://localhost:8000/health && printf "\n$(GREEN)✓ API is healthy$(RESET)\n" || printf "\n$(RED)✗ API is not responding$(RESET)\n"

routes: ## List all registered API routes
	@docker compose exec nexus-writer uv run python -c "\
		from main import app; \
		routes = sorted(set((r.path, ','.join(r.methods - {'HEAD','OPTIONS'})) for r in app.routes if hasattr(r, 'methods'))); \
		[print(f'  {m:8s} {p}') for p, m in routes]"

## --- Database
.PHONY: start-db stop-db reset-db dbshell migrate upgrade migrate-history dump-db restore-db

start-db: ## Start only PostgreSQL
	./dev_scripts/start_db.sh

stop-db: ## Stop PostgreSQL (removes volume)
	./dev_scripts/stop_db.sh

reset-db: ## Reset PostgreSQL (destroy + recreate)
	./dev_scripts/reset_db.sh

dbshell: ## Open psql shell in the database
	./dev_scripts/dbshell.sh

migrate: ## Create a new migration (usage: make migrate name=add_field)
	./dev_scripts/migrate.sh $(name)

upgrade: ## Apply pending migrations
	./dev_scripts/upgrade.sh

migrate-history: ## Show applied migration history
	@docker compose exec postgres-nexus psql -U nexus_user -d nexus_writer -c "SELECT * FROM aerich ORDER BY id;"

dump-db: ## Dump database to backups/nexus_dump.sql
	@mkdir -p backups
	@docker compose exec postgres-nexus pg_dump -U nexus_user nexus_writer > backups/nexus_dump_$$(date +%Y%m%d_%H%M%S).sql
	@printf "$(GREEN)✓ Database dumped to backups/$(RESET)\n"

restore-db: ## Restore database from a dump (usage: make restore-db file=backups/dump.sql)
	@test -f $(file) || (printf "$(RED)✗ Specify file: make restore-db file=backups/dump.sql$(RESET)\n" && exit 1)
	@docker compose exec -T postgres-nexus psql -U nexus_user -d nexus_writer < $(file)
	@printf "$(GREEN)✓ Database restored from $(file)$(RESET)\n"

## --- Logs & Debug
.PHONY: logs logs-err shell

logs: ## Follow container logs (usage: make logs s=nexus-writer)
	docker compose logs -f $(or $(s),nexus-writer)

logs-err: ## Tail the application error log
	@tail -f logs/errors.log 2>/dev/null || printf "$(YELLOW)No error log found yet$(RESET)\n"

shell: ## Open a bash shell in the API container
	./dev_scripts/shell.sh

## --- Workers
.PHONY: start-workers stop-workers restart-workers rebuild-workers logs-workers worker-status

start-workers: ## Start the session worker container
	docker compose up -d session_worker

stop-workers: ## Stop the session worker container
	docker compose stop session_worker

restart-workers: ## Restart the session worker container
	docker compose restart session_worker

rebuild-workers: ## Rebuild and restart the session worker container
	docker compose up -d --build session_worker

logs-workers: ## Follow logs for the session worker
	docker compose logs -f session_worker

worker-status: ## Show health status of the session worker
	@docker compose ps session_worker --format "table {{.Name}}\t{{.Status}}"

## --- Code Quality
.PHONY: lint format typecheck

lint: ## Run ruff linter
	@uv run ruff check src/ main.py session_worker.py

format: ## Auto-format code with ruff
	@uv run ruff format src/ main.py session_worker.py
	@uv run ruff check --fix src/ main.py session_worker.py

typecheck: ## Run mypy type checking
	@uv run mypy src/ main.py session_worker.py

## --- Dependencies
.PHONY: install install-dev outdated update-deps check-deps

install: ## Install project dependencies
	@uv sync

install-dev: ## Install with dev dependencies (lint, typecheck)
	@uv add --dev ruff mypy

outdated: ## Show outdated packages
	@uv pip list --outdated 2>/dev/null || uv run pip list --outdated

update-deps: ## Update all dependencies to latest compatible versions
	@uv lock --upgrade
	@uv sync
	@printf "$(GREEN)✓ Dependencies updated$(RESET)\n"

check-deps: ## Check for dependency conflicts
	@uv pip check && printf "$(GREEN)✓ No conflicts$(RESET)\n" || printf "$(RED)✗ Conflicts found$(RESET)\n"

## --- Housekeeping
.PHONY: clean fresh env-check

clean: ## Remove __pycache__, .pyc, .pyo files
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@printf "$(GREEN)✓ Cleaned$(RESET)\n"

fresh: ## Nuclear option: reset DB + full rebuild
	@printf "$(RED)⚠ This will destroy all data and rebuild everything.$(RESET)\n"
	@printf "Press Ctrl+C to cancel, or wait 5 seconds...\n"
	@sleep 5
	docker compose down -v
	docker compose up --build -d
	docker compose logs nexus-writer -f

env-check: ## Verify .env file exists and show keys (no values)
	@test -f .env && (printf "$(GREEN)✓ .env found$(RESET)\n" && awk -F= '/^[^#]/ {printf "  %s\n", $$1}' .env) || printf "$(RED)✗ .env file not found$(RESET)\n"