FROM conda/miniconda3

USER root
ARG AMAZON_BUCKET=serenata-de-amor-data
ARG AMAZON_REGION=sa-east-1

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
