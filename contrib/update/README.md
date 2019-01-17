This directory contains files to automatically run Rosie and update Jarbas.

To run it set the DigitalOcean API token in `.env` and then:

```console
$ docker build -t serenata-update .
$ docker run -it --rm --env-file .env serenata-update
```
