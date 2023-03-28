.PHONY: rs migrate dump shell seed collect_insights compilereqtxt clean

rs:
	python manage.py runserver

migrate:
	python manage.py migrate
	python manage.py migrate insights --database=insights

shell:
	python manage.py shell

seed:
	python manage.py seed_db

collect_insights:
	python manage.py collect_insights

compilereq:
	python requirements/compile.py

clean:
	rm -f db/*.db
	rm -rf django_insights/migrations
	rm -rf project/testapp/migrations

	python manage.py makemigrations testapp users
	python manage.py makemigrations insights
	python manage.py migrate
	python manage.py migrate insights --database=insights