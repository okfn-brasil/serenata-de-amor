FROM continuumio/conda-ci-linux-64-python3.7

ENTRYPOINT ["/opt/conda/bin/python"]

ARG AMAZON_BUCKET=serenata-de-amor-data
ARG AMAZON_ENDPOINT=https://nyc3.digitaloceanspaces.com
ARG AMAZON_REGION=nyc3

WORKDIR /code
COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY rosie.py ./
COPY rosie ./rosie
