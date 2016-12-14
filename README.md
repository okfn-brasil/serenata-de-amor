# Rosie, the robot

A Python application reading receipts from the Quota for Exercising Parliamentary Activity (aka CEAP, from the Brazilian Chamber of Deputies) and outputs, for each of the receipts, a "probability of corruption" and a list of reasons why is considered this way.

- [x] Fetch CEAP dataset from Chamber of Deputies
- [x] Convert XML to CSV
- [x] Translate CSVs to English
- [x] Read CEAP dataset from CSV into Pandas
- [ ] Process in the "corruption pipeline"
    - [ ] Monthly limits - quota
    - [x] Monthly limits - subquota
    - [ ] Machine Learning models using scikit-learn
- [ ] Task to push to Jarbas via API

## Setup

```console
$ cd rosie
$ conda update conda
$ conda create --name serenata_rosie python=3
$ source activate serenata_rosie
$ ./setup
```

## Running

```console
$ python rosie.py run
```

A `/tmp/serenata-data/irregularities.xz` file will be created. It's a compacted CSV with all the irregularities Rosie is able to find.

Also a target directory (where files are saved) can de passed — for example:

```console
$ python rosie.py run /my/serenata/directory/
```

## Test suite

```console
$ python rosie.py test
```
