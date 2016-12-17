FROM python:3.5
COPY requirements.txt /requirements.txt
RUN python -m pip install -U pip
RUN python -m pip install -r requirements.txt
RUN apt-get update && apt-get install -y postgresql postgresql-contrib
COPY .env /code/.env
COPY manage.py /code/manage.py
COPY jarbas /code/jarbas
WORKDIR /code
RUN echo "America/Sao_Paulo" > /etc/timezone && dpkg-reconfigure -f noninteractive tzdata
VOLUME /code/staticfiles
CMD ["gunicorn", "jarbas.wsgi:application", "--reload", "--bind", "0.0.0.0:8001", "--workers", "4"]
