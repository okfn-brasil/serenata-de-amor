FROM python:3.5.4-alpine
ENV PYTHONUNBUFFERED=1 \
    GOSS_VERSION=${GOSS_VERSION:-v0.3.5}

COPY ./requirements.txt /code/requirements.txt
COPY ./requirements-dev.txt /code/requirements-dev.txt
COPY manage.py /code/manage.py
COPY jarbas /code/jarbas
COPY goss.yaml /goss/goss.yaml

WORKDIR /code

# set timezone
RUN set -ex && \
    apk add --no-cache --virtual=.goss-dependencies curl ca-certificates && \
    curl -L https://github.com/aelsabbahy/goss/releases/download/"$GOSS_VERSION"/goss-linux-amd64 -o /usr/local/bin/goss && \
    chmod +rx /usr/local/bin/goss && \
    apk update && apk add --no-cache tzdata libpq && \
    cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    echo "America/Sao_Paulo" >  /etc/timezone && \
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
    apk del --purge .build-dependencies .goss-dependencies

HEALTHCHECK --interval=1m --timeout=2m CMD goss -g /goss/goss.yaml validate
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
