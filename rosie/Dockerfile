FROM alpine:3.6

ARG AMAZON_BUCKET=serenata-de-amor-data
ARG AMAZON_REGION=sa-east-1

COPY requirements.txt ./
COPY rosie.py ./
COPY rosie ./rosie

RUN apk add --no-cache python3 libstdc++ lapack && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    apk add --no-cache \
        --virtual=.build-dependencies \
        g++ gfortran musl-dev lapack-dev \
        python3-dev ca-certificates  libxslt-dev libxml2-dev && \
    ln -s locale.h /usr/include/xlocale.h && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    pip install -r requirements.txt && \
    find /usr/lib/python3.*/ -name 'tests' -exec rm -r '{}' + && \
    rm /usr/include/xlocale.h && \
    rm -r /root/.cache && \
    apk del --purge .build-dependencies
