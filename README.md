# Jarbas — a tool for [Serenata de Amor](http://github.com/datasciencebr/serenata-de-amor)


[Jarbas](http://serenata-jarbas.herokuapp.com/) is a tool for [Serenata de Amor](http://github.com/datasciencebr/serenata-de-amor).

For a JSON API try `GET /api/document/<document_id>` or [just browse](http://serenata-jarbas.herokuapp.com/) with your favorite browser.

## Install

### Requirements

The app is based in [Python 3](http://python.org) and [Node.js](http://nodejs.org). Once you have `pip` and `npm` available, install the dependencies:

```console
npm i
python -m pip install -r requirements.txt
```

### Settings

Copy `contrib/.env.sample` as `.env` in the project's root folder and adjust your settings. These are the main environment settings:

#### Django settings

* `DEBUG` (_bool_) enable or disable [Django debug mode](https://docs.djangoproject.com/en/1.9/ref/settings/#debug)
* `SECRET_KEY` (_str_) [Django's secret key](https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-SECRET_KEY)
* `ALLOWED_HOSTS` (_str_) [Django's allowed hosts](https://docs.djangoproject.com/en/1.9/ref/settings/#allowed-hosts)

#### Database

* `DATABASE_URL` (_string_) [Database URL](https://github.com/kennethreitz/dj-database-url#url-schema)
* `DATABASE_LIMIT` (_int_) Limit the number of documents to import to your database (`0` for unlimited)

#### Amazon S3 settings

* `AMAZON_S3_BUCKET` (_str_) Name of the Amazon S3 bucket to look for datasets (e.g. `serenata-de-amor-data`)
* `AMAZON_S3_REGION` (_str_) Region of the Amazon S3 (e.g. `s3-sa-east-1`)
* `AMAZON_S3_DATASET_DATE` (_str_) Datasets file name prefix (e.g. `2016-08-08` for `2016-08-08-current-year.xz`)

### Migrations

Once you're done with requirements, dependencies and settings, create the basic structure at the database (and if you like create a super-user for you, so you can use [Django Admin](http://localhost:8000/admin) later):

```console
python manage.py migrate
python manage.py createsuperuser
```

### Generate static files

We generate assets through [webassets](http://webassets.readthedocs.io) and we serve static files through [WhiteNoise](http://whitenoise.evans.io), thus you might have to run:

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