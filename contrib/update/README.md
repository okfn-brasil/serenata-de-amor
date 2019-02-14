# Serenata Update

This directory contains files to automatically run Rosie and update Jarbas.

## Requirements

* [Python](https://python.org) 2 binary available (see [Warning](#warning))
* [Pipenv](https://pipenv.readthedocs.io/)

Then install the required Python packages:

```console
$ pipenv install
```

## Settings

Copy `.env.sample` as `.env` and set the following variables:

| Name | Description |
|:-----|:------------|
| `DO_API_TOKEN` | DigitalOcean' API token |
| `DO_SSH_KEY_NAME` | Name of a SSH key registered at DigitalOcean |
| `DATABASE_URL`| Credentials for Jarba's production database |

## Running

To run Rosie and automatically update Jarbas:

```console
$ pipenv run ansible-playbook update.yml
```

```console
$ pipenv run python cleanup.py
```

## Warning

This module is based on Python 2 since:

* The [`dopy`](https://pypi.org/project/dopy/) Python package Ansible depends on is
  [only available in Python 2](https://github.com/Wiredcraft/dopy/issues/61), and is not updated in ages
* We could use a fork, but we
  [would need to trust the fork owner](https://github.com/okfn-brasil/serenata-de-amor/pull/449#discussion_r253397600)
* Maintaining a fork is out of our scope at the moment

However, Ansible is already
[migrating for an alternative package](https://github.com/ansible/ansible/pull/33984)
and soon (before the end of life of Python 2) we will be able to update. This new module is already merged, but not released yet.