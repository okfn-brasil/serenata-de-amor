FROM conda/miniconda3

ARG AMAZON_BUCKET=serenata-de-amor-data
ARG AMAZON_REGION=sa-east-1

COPY requirements.txt ./
COPY rosie.py ./

RUN pip install -r requirements.txt

COPY rosie ./rosie
