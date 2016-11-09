FROM python:3.5
COPY requirements-dev.txt /requirements-dev.txt
RUN python -m pip install -r requirements-dev.txt
COPY ./ /code
WORKDIR /code
RUN python manage.py migrate
RUN python manage.py createsuperuser
RUN python manage.py loaddatasets
RUN python manage.py loadsuppliers
RUN python manage.py ceapdatasets
RUN python manage.py assets build
RUN python manage.py collectstatic
