FROM python:2.7.15-slim

WORKDIR /serenata-update

COPY requirements.txt requirements.txt

RUN apt-get update && \
    apt-get install -y  openssh-client && \
    /usr/bin/ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa && \
    chmod 700 /root/.ssh && \
    chmod 644 /root/.ssh/id_rsa.pub && \
    chmod 600 /root/.ssh/id_rsa && \
    apt-get remove -y openssh-client && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -U pip && \
    pip install -r requirements.txt

COPY ansible.cfg ansible.cfg
COPY cleanup.py cleanup.py
COPY update.yml update.yml
CMD ["ansible-playbook", "update.yml"]
