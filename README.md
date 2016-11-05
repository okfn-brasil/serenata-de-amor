# Jarbas — a tool for [Serenata de Amor](http://github.com/datasciencebr/serenata-de-amor)

[![Build Status](https://travis-ci.org/datasciencebr/jarbas.svg?branch=master)](https://travis-ci.org/datasciencebr/jarbas)
[![Code Climate](https://codeclimate.com/github/datasciencebr/jarbas/badges/gpa.svg)](https://codeclimate.com/github/datasciencebr/jarbas)
[![Coverage Status](https://coveralls.io/repos/github/datasciencebr/jarbas/badge.svg?branch=master)](https://coveralls.io/github/datasciencebr/jarbas?branch=master)
[![Updates](https://pyup.io/repos/github/datasciencebr/jarbas/shield.svg)](https://pyup.io/repos/github/datasciencebr/jarbas/)

[Jarbas](http://jarbas.datasciencebr.com/) is a tool for [Serenata de Amor](http://github.com/datasciencebr/serenata-de-amor) contributors.

## JSON API endpoints

### Documents

In Jarbas context a `Document` refers to a document (a reimbursement claim) from [CEAP](http://www2.camara.leg.br/participe/fale-conosco/perguntas-frequentes/cota-para-o-exercicio-da-atividade-parlamentar).

#### `GET /api/document/`

This endpoint lists `Document` objects and it accepts any field (and any combination among them) as a filter. For example:

`GET /api/document/?year=2015&state=RS&congressperson_id=42`

These are the fields that can be combined for filtering purposes:

* `applicant_id`
* `cnpj_cpf`
* `congressperson_id`
* `document_id`
* `document_type`
* `month`
* `party`
* `reimbursement_number`
* `state`
* `subquota_group_id`
* `subquota_number`
* `term`
* `year`

#### `GET /api/receipt/<Document.pk>`

This endpoint gets the URL to the digitalized version of the receipt of a `Document`. It returns `{ url: null }` if the digitalized version is not available. The endpoint expects a `Document.pk` (i.e. the primary key of the `Document` object).

### Supplier

A supplier is a Brazilian company in which congressperson have made expenses and claimed for reimbursement.

#### `GET /api/supplier/<Supplier.cnpj>`

This endpoit gets the info we have for a specific supplier. The endpoint expects a `Supplier.cnpj` (i.e. the CNPJ of a `Supplier` object). It returns `404` if the supplier is not found.

### Tapioca Jarbas

There's also a tapioca-wrapper for the API, the [tapioca-jarbas](https://github.com/daneoshiga/tapioca-jarbas/) can be installed with `pip install tapioca-jarbas` and can be used to access the API in python scripts.


## Install

### Requirements

The app is based in [Python 3.5](http://python.org) and [Node.js 6](http://nodejs.org). Once you have `pip` and `npm` available, install the dependencies:

```console
npm i
python -m pip install -r requirements-dev.txt
```

Minor details on requirements:

* **`lzma`**: In some Linux distros `lzma` is not installed by default. You can check whether you have it or not with `$ python -m lzma`. In Debian based systems you can fix that with `$ apt-get install liblzma-dev` but you mihght have to re-compile your Python.
* **`elm-make`**: If `elm-make` is not available in your path, or if the `elm-make` version differs from [the one required by this project](packages.json), set [`ELM_MAKE_BIN`](https://github.com/cuducos/webassets-elm#requirements) environment variable pointing to where the proper `elm-make` binary is (probably `node_modules/.bin/elm-make`)
* **`psycopg2`**: The `requirements.txt` file is prepared to use [PostgresSQL](https://www.postgresql.org) and `psycopg2` might fail if you don't have Postgres installed locally.

### Settings

Copy `contrib/.env.sample` as `.env` in the project's root folder and adjust your settings. These are the main environment settings:

#### Django settings

* `DEBUG` (_bool_) enable or disable [Django debug mode](https://docs.djangoproject.com/en/1.10/ref/settings/#debug)
* `SECRET_KEY` (_str_) [Django's secret key](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-SECRET_KEY)
* `ALLOWED_HOSTS` (_str_) [Django's allowed hosts](https://docs.djangoproject.com/en/1.10/ref/settings/#allowed-hosts)
* `USE_X_FORWARDED_HOST` (_bool_) [Whether to use the `X-Forwarded-Host` header](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-USE_X_FORWARDED_HOST)

#### Database

* `DATABASE_URL` (_string_) [Database URL](https://github.com/kennethreitz/dj-database-url#url-schema)

#### Amazon S3 settings

* `AMAZON_S3_BUCKET` (_str_) Name of the Amazon S3 bucket to look for datasets (e.g. `serenata-de-amor-data`)
* `AMAZON_S3_REGION` (_str_) Region of the Amazon S3 (e.g. `s3-sa-east-1`)
* `AMAZON_S3_DATASET_DATE` (_str_) Datasets file name prefix of CEAP datasets from Serenata de Amor (e.g. `2016-08-08` for `2016-08-08-current-year.xz`)
* `AMAZON_S3_SUPPLIERS_DATE` (_str_) Datasets file name prefix for suppliers dataset (e.g. `2016-08-08` for `2016-08-08-companies.xz`)

#### Google settings

* `GOOGLE_ANALYTICS` (_str_) Google Analytics tracking code (e.g. `UA-123456-7`)
* `GOOGLE_STREET_VIEW_API_KEY` (_str_) Google Street View Image API key

### Migrations

Once you're done with requirements, dependencies and settings, create the basic structure at the database (and if you wish, create a super-user for you, so you can use [Django Admin](http://localhost:8000/admin) later):

```console
python manage.py migrate
python manage.py createsuperuser
```

### Load data

Now you can load the data from our datasets:

```
python manage.py loaddatasets
python manage.py loadsuppliers
python manage.py ceapdatasets
```

Use `python manage.py loaddatasets --help` and ``python manage.py loadsuppliers --help` to check options on limiting the number of documents to be loaded from the datasets.

### Generate static files

We generate assets through [webassets](http://webassets.readthedocs.io) thus you might have to run:

```console
python manage.py assets build
python manage.py collectstatic
```

### Ready?

Not sure? Run `python manage.py check` and `python manage.py test` just in case.

### Ready!

Run the server with `python manage.py runserver` and load [localhost:8000](http://localhost:8000) in your favorite browser.

If you created a _super-user_ account, you can also use [Django Admin](https://docs.djangoproject.com/en/stable/ref/contrib/admin/) at [`/admin/`](http://localhost:8000/admin/).

## License

Licensed under the [MIT License](LICENSE).
