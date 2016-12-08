FROM jupyter/datascience-notebook:latest
MAINTAINER Serenata de Amor "datasciencebr@gmail.com"

USER root

RUN apt-get update \
    && apt-get install unzip -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY conda_requirements.txt ./
RUN conda update --yes conda \
    && conda config --add channels Rufone \
    && conda config --add channels conda-forge \
    && conda install --yes --file conda_requirements.txt \
    && conda clean -tipsy

COPY docker/jupyter_notebook_config.py /home/jovyan/.jupyter/jupyter_notebook_config.py
