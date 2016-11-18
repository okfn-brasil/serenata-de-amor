### Makefile to provision Jarbas infra

run.jarbas:
	docker-compose up -d

collect.statics: run.jarbas
	docker-compose run --rm jarbas python manage.py collectstatic --no-input

run.devel: collect.statics
