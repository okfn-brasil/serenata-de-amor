FROM jupyter/datascience-notebook:bb222f49222e
MAINTAINER Serenata de Amor "datasciencebr@gmail.com"

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                       unzip \
                       libxml2-dev \
                       libxslt-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY docker/jupyter_notebook_config.py /home/jovyan/.jupyter/jupyter_notebook_config.py
