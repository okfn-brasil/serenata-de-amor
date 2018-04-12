# Rosie, the robot

[![Build Status](https://travis-ci.org/datasciencebr/rosie.svg?branch=master)](https://travis-ci.org/datasciencebr/rosie)
[![Code Climate](https://codeclimate.com/github/datasciencebr/rosie/badges/gpa.svg)](https://codeclimate.com/github/datasciencebr/rosie)
[![Coverage Status](https://coveralls.io/repos/github/datasciencebr/rosie/badge.svg?branch=master)](https://coveralls.io/github/datasciencebr/rosie?branch=master)
[![Updates](https://pyup.io/repos/github/datasciencebr/rosie/shield.svg)](https://pyup.io/repos/github/datasciencebr/rosie/)
[![donate](https://img.shields.io/badge/donate-apoia.se-EB4A3B.svg)](https://apoia.se/serenata)
[![Follow](https://img.shields.io/twitter/follow/RosieDaSerenata.svg?style=social&label=Follow)](https://twitter.com/RosieDaSerenata)

A Python application reading receipts from the [Quota for Exercising Parliamentary Activity](https://github.com/datasciencebr/serenata-de-amor/blob/master/CONTRIBUTING.md#more-about-the-quota-for-exercising-parliamentary-activity-ceap) (aka CEAP) from the Brazilian Chamber of Deputies and outputs, for each of the receipts, a _probability of corruption_ and a list of reasons why it was considered this way.

## Running

### With Docker

```console
$ docker run --rm -v /tmp/serenata-data:/tmp/serenata-data datasciencebr/rosie run <module_name>
```

Then check your `/tmp/serenata-data/` directory in you host machine for `irregularities.xz`.

For testing

```console
$ docker run --rm -v /tmp/serenata-data:/tmp/serenata-data datasciencebr/rosie test
```

### Without Docker

#### Setup

```console
$ conda update conda
$ conda create --name serenata_rosie python=3
$ source activate serenata_rosie
$ ./setup
```

#### Running

To run Rosie, you need to select a module to be called.
For example, if you want to run `chamber_of_deputies` module, you should run this command:

```console
$ python rosie.py run chamber_of_deputies
```

A `/tmp/serenata-data/irregularities.xz` file will be created. It's a compacted CSV with all the irregularities Rosie is able to find.

Also a target directory (where files are saved) can de passed — for example:

```console
$ python rosie.py run chamber_of_deputies /my/serenata/directory/
```

#### Test suite

You can either run all tests with:
```console
$ python rosie.py test
```

Or test each submodule a time by passing a name:
```console
$ python rosie.py test core
$ python rosie.py test chamber_of_deputies
$ python rosie.py test federal_senate
```
