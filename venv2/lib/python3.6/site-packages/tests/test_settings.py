import os
import dj_database_url

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), os.pardir)

SECRET_KEY = 'not_so_secret_r2fetCebUAZB3DhzTn5NPg8J08IancuGt04npTMh'
DEBUG = True

db_url = os.environ.get("DATABASE_URL", "sqlite://localhost/:memory:")
DB = dj_database_url.parse(db_url)

DATABASES = {
    # 'default': DB,

    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'default',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

INSTALLED_APPS = ('django_bulk_update', 'tests',)
MIDDLEWARE_CLASSES = ()
