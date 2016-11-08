FROM jupyter/datascience-notebook:latest
MAINTAINER Serenata de Amor "datasciencebr@gmail.com"

USER root

RUN apt-get update && apt-get install -y \
  unzip

USER jovyan

COPY requirements.txt ./
COPY conda_requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN conda update --yes conda
RUN conda config --add channels Rufone
RUN conda config --add channels conda-forge
RUN conda install --yes --file conda_requirements.txt
