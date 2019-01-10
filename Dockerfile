FROM python:3.6.4-alpine3.7

ENV AMAZON_BUCKET=serenata-de-amor-data \
    AMAZON_REGION=sa-east-1 \
    PYTHONUNBUFFERED=1 \
    SECRET_KEY=${SECRET_KEY:-my-secret}

COPY ./requirements.txt /code/requirements.txt
COPY ./requirements-dev.txt /code/requirements-dev.txt
COPY manage.py /code/manage.py
COPY jarbas /code/jarbas

WORKDIR /code

RUN set -ex && \
    apk update && apk add --no-cache curl tzdata libpq && \
    cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    echo "America/Sao_Paulo" > /etc/timezone && \
    apk update && apk add --no-cache \
      --virtual=.build-dependencies \
      gcc \
      musl-dev \
      postgresql-dev \
      git \
      python3-dev && \
    python -m pip --no-cache install -U pip && \
    python -m pip --no-cache install -r requirements-dev.txt && \
    python manage.py collectstatic --no-input && \
    apk del --purge .build-dependencies

HEALTHCHECK --interval=1m --timeout=2m CMD curl 0.0.0.0:8000/healthcheck/
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
