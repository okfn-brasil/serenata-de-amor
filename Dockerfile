FROM python:3.5
USER root
RUN apt-get update && apt-get install -y \
  build-essential \
  libxml2-dev \
  libxslt1-dev \
  python3-dev \
  unzip \
  zlib1g-dev
  
RUN pip install --upgrade pip
COPY requirements.txt ./
COPY setup ./
RUN ./setup
COPY rosie.py ./
COPY rosie ./rosie

CMD python rosie.py run
