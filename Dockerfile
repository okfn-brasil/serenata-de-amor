FROM alpine:3.6

LABEL maintainer="https://github.com/datasciencebr/rosie"

COPY requirements.txt ./
COPY setup ./
COPY rosie.py ./
COPY rosie ./rosie
COPY config.ini.example ./

RUN apk add --no-cache python3 libstdc++ lapack && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    apk add --no-cache \
        --virtual=.build-dependencies \
        g++ gfortran musl-dev lapack-dev \
        python3-dev ca-certificates  libxslt-dev libxml2-dev && \
    ln -s locale.h /usr/include/xlocale.h && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ./setup && \
    find /usr/lib/python3.*/ -name 'tests' -exec rm -r '{}' + && \
    rm /usr/include/xlocale.h && \
    rm -r /root/.cache && \
    apk del --purge .build-dependencies

ENTRYPOINT ["python", "rosie.py"]
