.PHONY: lint rs migrate dump shell seed collect_insights clean docs-build docs-serve

# Docs with dokk, run through uvx so it is not a project dependency
DOKK = uvx --from 'dokk[serve,search]==0.0.4' dokk

rs:
	uv run python manage.py runserver

migrate:
	mkdir -p db
	uv run python manage.py migrate
	uv run python manage.py migrate insights --database=insights

shell:
	uv run python manage.py shell

seed:
	uv run python manage.py seed_db

collect_insights:
	uv run python manage.py collect_insights

lint:
	uv run ruff check --fix .
	uv run ruff format .
	uv run ty check
	uv run pytest

clean:
	rm -f db/*.db
	$(MAKE) migrate

docs-build:
	$(DOKK) check
	$(DOKK) build

docs-serve:
	$(DOKK) serve
