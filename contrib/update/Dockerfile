FROM python:3.7.2-alpine

WORKDIR /serenata-update

COPY requirements.txt requirements.txt

RUN apk update && \
    apk add openssh-keygen openssl-dev && \
    /usr/bin/ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa && \
    chmod 700 /root/.ssh && \
    chmod 644 /root/.ssh/id_rsa.pub && \
    chmod 600 /root/.ssh/id_rsa && \
    apk add --virtual .build-dependencies \
        build-base \
        git \
        libffi-dev && \
    pip install -U pip && \
    pip install -r requirements.txt && \
    apk del .build-dependencies

COPY ansible.cfg ansible.cfg
COPY cleanup.py cleanup.py
COPY update.yml update.yml
CMD ["ansible-playbook", "update.yml"]
