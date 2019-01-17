FROM python:3.7.2-alpine

WORKDIR /serenata-update

ADD requirements.txt requirements.txt

RUN apk update && \
    apk add --virtual .build-dependencies \
        build-base \
        git \
        libffi-dev \
        openssl-dev && \
    pip install -U pip && \
    pip install -r requirements.txt && \
    apk del .build-dependencies

ADD update.yml update.yml
CMD ["ansible-playbook", "update.yml"]
