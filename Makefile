.PHONY: lint rs migrate dump shell seed collect_insights clean

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
	rm -rf django_insights/migrations
	rm -rf project/testapp/migrations

	uv run python manage.py makemigrations testapp users
	uv run python manage.py makemigrations insights
	uv run python manage.py migrate
	uv run python manage.py migrate insights --database=insights