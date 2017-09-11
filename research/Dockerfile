FROM jupyter/datascience-notebook:8f56e3c47fec
MAINTAINER Serenata de Amor "datasciencebr@gmail.com"

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unzip \
        libxml2-dev \
        libxslt-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN sudo -u jovyan mkdir /home/jovyan/.jupyter

USER jovyan

COPY ./research/requirements.txt ./requirements.txt
COPY ./config.ini ./config.ini
COPY ./setup ./setup

RUN conda update setuptools
RUN pip install -r requirements.txt
RUN ./setup

COPY ./research/jupyter_notebook_config.py /home/jovyan/.jupyter/jupyter_notebook_config.py
