# Jarbas — a tool for [Serenata de Amor](http://github.com/datasciencebr/serenata-de-amor)

[![Build Status](https://travis-ci.org/datasciencebr/jarbas.svg?branch=master)](https://travis-ci.org/datasciencebr/jarbas)
[![Code Climate](https://codeclimate.com/github/datasciencebr/jarbas/badges/gpa.svg)](https://codeclimate.com/github/datasciencebr/jarbas)
[![Coverage Status](https://coveralls.io/repos/github/datasciencebr/jarbas/badge.svg?branch=master)](https://coveralls.io/github/datasciencebr/jarbas?branch=master)
[![Updates](https://pyup.io/repos/github/datasciencebr/jarbas/shield.svg)](https://pyup.io/repos/github/datasciencebr/jarbas/)

[Jarbas](http://jarbas.datasciencebr.com/) is part of [Serenata de Amor](http://github.com/datasciencebr/serenata-de-amor) — we fight corruption with data science.

Jarbas is in charge of making data from [CEAP](https://github.com/datasciencebr/serenata-de-amor/blob/master/CONTRIBUTING.md#more-about-the-quota-for-exercising-parliamentary-activity-ceap) more accessible. In the near future Jarbas will show what [Rosie](https://github.com/datasciencebr/rosie) thinks of each reimbursement made for our congresspeople.

## Table of Contents

1. [JSON API endpoints](#json-api-endpoints)
    1. [Documents](#documents)
    1. [Supplier](#supplier)
    1. [Tapioca Jarbas](#tapioca-jarbas)
1. [Installing](#installing)
    1. [Using Docker](#using-docker)
    1. [Local install](#local-install)
 
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

There is also a [tapioca-wrapper](https://github.com/vintasoftware/tapioca-wrapper) for the API. The [tapioca-jarbas](https://github.com/daneoshiga/tapioca-jarbas/) can be installed with `pip install tapioca-jarbas` and can be used to access the API in any Python script.

## Installing

### Using Docker

If you have [Docker](https://docs.docker.com/engine/installation/) (with [Docker Compose](https://docs.docker.com/compose/install/)) and make, jusr run:

```console
$ docker-compose up -d
```


You can access it at [`localhost:80`](http://localhost:80/). However your database starts empty and you still have to collect your static files:

```console
$ docker-compose run --rm jarbas python manage.py collectstatic --no-input
$ docker-compose run --rm jarbas python manage.py loaddatasets
$ docker-compose run --rm jarbas python manage.py loadsupliers

```

There are some cleaver shortcuts in the `Makefile` if you like it.

### Local install

#### Requirements

The app is based in [Python 3.5](http://python.org) and [Node.js 6](http://nodejs.org). Once you have `pip` and `npm` available, install the dependencies:

```console
npm i
python -m pip install -r requirements.txt
```

Minor details on requirements:

* **`lzma`**: In some Linux distros `lzma` is not installed by default. You can check whether you have it or not with `$ python -m lzma`. In Debian based systems you can fix that with `$ apt-get install liblzma-dev` but you mihght have to re-compile your Python. Some macOS Users might have the same problem. To check if you have `lzma` you can use `$ python -m lmza`. To fix it you need to install `lzma` using `$ brew install xz` and after that you need to recompile Python, and an way to do it is through `$ brew upgrade --cleanup python`.
* **`psycopg2`**: The `requirements.txt` file is prepared to use [PostgresSQL](https://www.postgresql.org) and `psycopg2` might fail if you don't have Postgres installed locally.

#### Settings

Copy `contrib/.env.sample` as `.env` in the project's root folder and adjust your settings. These are the main environment settings:

##### Django settings

* `DEBUG` (_bool_) enable or disable [Django debug mode](https://docs.djangoproject.com/en/1.10/ref/settings/#debug)
* `SECRET_KEY` (_str_) [Django's secret key](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-SECRET_KEY)
* `ALLOWED_HOSTS` (_str_) [Django's allowed hosts](https://docs.djangoproject.com/en/1.10/ref/settings/#allowed-hosts)
* `USE_X_FORWARDED_HOST` (_bool_) [Whether to use the `X-Forwarded-Host` header](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-USE_X_FORWARDED_HOST)

##### Database

* `DATABASE_URL` (_string_) [Database URL](https://github.com/kennethreitz/dj-database-url#url-schema)

##### Amazon S3 settings

* `AMAZON_S3_BUCKET` (_str_) Name of the Amazon S3 bucket to look for datasets (e.g. `serenata-de-amor-data`)
* `AMAZON_S3_REGION` (_str_) Region of the Amazon S3 (e.g. `s3-sa-east-1`)
* `AMAZON_S3_DATASET_DATE` (_str_) Datasets file name prefix of CEAP datasets from Serenata de Amor (e.g. `2016-08-08` for `2016-08-08-current-year.xz`)
* `AMAZON_S3_SUPPLIERS_DATE` (_str_) Datasets file name prefix for suppliers dataset (e.g. `2016-08-08` for `2016-08-08-companies.xz`)
* `AMAZON_S3_CEAPTRANSLATION_DATE` (_str_) File name prefix for dataset guide (e.g. `2016-08-08` for `2016-08-08-ceap-datasets.md`)

##### Google settings

* `GOOGLE_ANALYTICS` (_str_) Google Analytics tracking code (e.g. `UA-123456-7`)
* `GOOGLE_STREET_VIEW_API_KEY` (_str_) Google Street View Image API key

#### Migrations

Once you're done with requirements, dependencies and settings, create the basic database structure:

```console
$ python manage.py migrate
```

#### Load data

Now you can load the data from our datasets and get some other data as static files:

```
$ python manage.py loaddatasets
$ python manage.py loadsuppliers
$ python manage.py ceapdatasets
```

Use `python manage.py loaddatasets --help` and `python manage.py loadsuppliers --help` to check options on limiting the number of documents to be loaded from the datasets.

#### Generate static files

We generate assets through NodeJS, so run it before Django collecting static files:

```console
$ npm run assets
$ python manage.py collectstatic

```

#### Ready?

Not sure? Test it!

```
$ npm run test
$ python manage.py check
$ python manage.py test
```

#### Ready!

Run the server with `$ python manage.py runserver` and load [localhost:8000](http://localhost:8000) in your favorite browser.