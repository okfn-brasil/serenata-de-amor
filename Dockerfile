FROM python:3.5.4-alpine
ENV PYTHONUNBUFFERED 1

# set timezone
RUN apk update && apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    echo "America/Sao_Paulo" >  /etc/timezone

# pyscopg2 dependencies
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    python3-dev

# install git so we can pip install from github repos
RUN apk update && apk add --no-cache git

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./requirements-dev.txt /code/requirements-dev.txt
RUN python -m pip install -U pip && \
    python -m pip install -r requirements-dev.txt

COPY manage.py /code/manage.py
COPY jarbas /code/jarbas
RUN python manage.py collectstatic --no-input

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
