FROM python:3.5
COPY requirements.txt /requirements.txt
RUN python -m pip install -U pip
RUN python -m pip install -r requirements.txt
RUN apt-get update && apt-get install -y postgresql postgresql-contrib
COPY ./ /code
WORKDIR /code
RUN python manage.py migrate
#RUN python manage.py ceapdatasets
RUN echo "America/Sao_Paulo" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata
VOLUME /code/staticfiles
CMD ["gunicorn", "jarbas.wsgi:application", "--reload", "--bind", "0.0.0.0:8001", "--workers", "4"]
