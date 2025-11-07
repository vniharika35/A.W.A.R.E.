PYTHON ?= python3
PIP ?= pip3

.PHONY: install lint type-check test api-test e2e docs-build docs-serve docs-live ci docker-build pre-commit-install run-api simulate leak-detect demo compose-up compose-down orchestrator

install:
	$(PIP) install -r requirements-dev.txt

pre-commit-install: install
	pre-commit install

lint:
	pre-commit run --all-files --hook-stage manual --show-diff-on-failure

type-check:
	mypy aware

test:
	pytest

api-test:
	pytest -m api || true

e2e:
	$(PYTHON) -m aware.agents > /dev/null

run-api:
	uvicorn aware.backend.app:app --reload --host 0.0.0.0 --port 8001

simulate:
	$(PYTHON) -m aware.sim --duration 600 --cadence 2

leak-detect:
	TELEMETRY=$${TELEMETRY:-docs/samples/telemetry_sample.csv} && \
	$(PYTHON) -m aware.ml $$TELEMETRY --baseline-window 90

demo:
	mkdir -p build
	$(PYTHON) -m aware.sim --duration 600 --cadence 5 --replay $${REPLAY_OUTPUT:-build/replay.csv}
	$(PYTHON) -m aware.agents > build/demo-events.json
	@echo "Demo artifacts saved under build/"

compose-up:
	docker compose up api db redis -d

compose-down:
	docker compose down

orchestrator:
	$(PYTHON) -m aware.agents

docs-build:
	mkdocs build -s

docs-serve:
	mkdocs serve -a 0.0.0.0:8000

ci: install lint type-check test api-test e2e docker-build

docker-build:
	docker build -t aware:dev .
