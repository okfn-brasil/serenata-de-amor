run.jarbas:
	docker-compose up -d

collectstatic: run.jarbas
	docker-compose run --rm jarbas python manage.py collectstatic --no-input

seed: run.jarbas
	docker-compose run --rm jarbas python manage.py loaddatasets
	docker-compose run --rm jarbas python manage.py loadsuppliers

run.devel: collectstatic
