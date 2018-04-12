FROM conda/miniconda3

USER root
ARG AMAZON_BUCKET=serenata-de-amor-data
ARG AMAZON_ENDPOINT=https://nyc3.digitaloceanspaces.com
ARG AMAZON_REGION=nyc3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unzip \
        libxml2-dev \
        libxslt-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /mnt/code

COPY ./requirements.txt ./requirements.txt
COPY ./setup ./setup

RUN pip install -r requirements.txt
RUN ./setup
