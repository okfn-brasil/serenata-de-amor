FROM jupyter/datascience-notebook:bb222f49222e
MAINTAINER Serenata de Amor "datasciencebr@gmail.com"

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unzip \
        libxml2-dev \
        libxslt-dev \
        libmagickwand-dev \
        ghostscript \
        libgtk2.0-dev\
        libffi-dev \
        libjpeg-turbo-progs \
        cmake \
        imagemagick\
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

COPY ./research/requirements.txt ./requirements.txt
COPY ./config.ini ./config.ini
COPY ./setup ./setup

RUN conda update setuptools
RUN pip install -r requirements.txt
RUN ./setup

COPY ./research/jupyter_notebook_config.py /home/jovyan/.jupyter/jupyter_notebook_config.py
