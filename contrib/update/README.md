# Serenata Update

This directory contains files to automatically run Rosie and update Jarbas.

To run it set the DigitalOcean API token in `.env` and then:

```console
$ docker build -t serenata-update .
$ docker run -it --rm --env-file .env serenata-update
```

## Warning

It is based on Python 2 since:

* The `dopy` Python package Ansible depends on is
  [only available in Python 2](https://github.com/Wiredcraft/dopy/issues/61)
* We could use a fork, but we
  [would need to trust the fork owner](https://github.com/okfn-brasil/serenata-de-amor/pull/449#discussion_r253397600)
* Maintaining a fork is out of our scope at the moment

However, Ansible is already
[migrating for an alternative package](https://github.com/ansible/ansible/pull/33984)
and soon (before the end of life of Python 2) we will be able to update.
