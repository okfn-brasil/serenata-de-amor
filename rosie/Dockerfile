FROM conda/miniconda3

ARG AMAZON_BUCKET=serenata-de-amor-data
ARG AMAZON_ENDPOINT=https://nyc3.digitaloceanspaces.com
ARG AMAZON_REGION=nyc3

WORKDIR /code
COPY requirements.txt ./
COPY rosie.py ./

RUN pip install -r requirements.txt

COPY rosie ./rosie
