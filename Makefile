run.jarbas:
	docker-compose up -d
	docker-compose run --rm jarbas python manage.py ceapdatasets
	docker-compose run --rm jarbas python manage.py migrate


collectstatic: run.jarbas
	docker-compose run --rm jarbas python manage.py collectstatic --no-input

seed.sample: run.jarbas
	docker-compose run --rm jarbas python manage.py reimbursements contrib/sample-data/reimbursements_sample.xz
	docker-compose run --rm jarbas python manage.py companies contrib/sample-data/companies_sample.xz
	docker-compose run --rm jarbas python manage.py suspicions contrib/sample-data/suspicions_sample.xz

run.devel: collectstatic

build.elm:
	docker-compose run elm
