run.jarbas:
	docker-compose up -d --build
	docker-compose run --rm jarbas python manage.py migrate
	docker-compose run --rm jarbas python manage.py ceapdatasets

collectstatic: run.jarbas
	docker-compose run --rm jarbas python manage.py collectstatic --no-input

seed: run.jarbas
	docker-compose run --rm jarbas python manage.py reimbursements /tmp/serenata-data/reimbursements.xz
	docker-compose run --rm jarbas python manage.py companies /tmp/serenata-data/2016-09-03-companies.xz
	docker-compose run --rm jarbas python manage.py irregularities /tmp/serenata-data/irregularities.xz

run.devel: collectstatic

build.elm:
	docker-compose run elm
