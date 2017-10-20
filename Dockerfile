FROM python:3.6-slim

COPY requirements.txt ./
COPY setup ./
COPY rosie.py ./
COPY rosie ./rosie
COPY config.ini.example ./

RUN apt-get update \ 
  && apt-get install apt-transport-https -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        python3 \
        python3-dev \
        unzip \
        zlib1g-dev \
  && pip install --upgrade pip \
  && ./setup \
  && apt-get purge -y --auto-remove apt-transport-https \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        python3-dev \
        zlib1g-dev \
  && rm -r /var/lib/apt/lists/* \
  && rm -Rf /root/.cache/pip


ENTRYPOINT ["python", "rosie.py"]
