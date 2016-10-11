# How to contribute?

## Before start

If you work with statistics but not a coder or a developer that are not used to the routine below or just willing to learn, share ideas and catch-up, join us in the [Telegram Open Group](http://bit.ly/2cUBFr6). This group keep their language in English to be internationally open and we make Telegram the official channel to make easy for non-developers to reach the technical group.

## The basic

A lot of discussions about ideas take place in the [Issues](https://github.com/datasciencebr/serenata-de-amor/issues) section. There you can catch up with what's going on and also suggest new ideas.

1. _Fork_ this repository
2. Create your branch: `$ git checkout -b new-stuff`
3. Commit your changes: `$ git commit -am 'My cool contribution'`
4. Push to the branch to your fork: `$ git push origin new-stuff`
5. Create a new _Pull Request_

## Environment

The recommended way of setting your environment up is with [Anaconda](https://www.continuum.io/), a Python distribution with useful packages for Data Science. [Download it](https://www.continuum.io/downloads) and create an _environment_ for the project.

```console
$ conda update conda
$ conda create --name serenata_de_amor python=3
$ source activate serenata_de_amor
$ ./setup
```

The `activate serenata_de_amor` command must be run every time you enter in the project folder to start working.

### Pyenv users

If you installed Anaconda via [pyenv](https://github.com/yyuu/pyenv) probably `source activate serenata_de_amor` will fail _unless_ you explicitly use the path to the Anaconta `activate` script. For example:

```console
$ source /usr/local/var/pyenv/versions/anaconda3-4.1.1/bin/activate serenata_de_amor
```

## Best practices

In order to avoid tons of conflicts when trying to merge [Jupyter Notebooks](http://jupyter.org), there are some [guidelines we follow](http://www.svds.com/jupyter-notebook-best-practices-for-data-science/).

Basically we have four big directories with different purposes:

| Directory | Purpose | File naming |
|-----------|---------|-------------|
| **`develop/`** | This is where we _explore_ data, feel free to create your own notebook for your exploration. | `[ISO 8601 date]-[author-initials]-[2-4 word description].ipynb` (e.g. `2016-05-13-ec-air-tickets.ipynb`) |
|**`report/`** | This is where we write up the findings and results, here is where we put together different data, analysis and strategies to make a point, feel free to jump in. | Meaninful title for the report (e.g. `Transport-allowances.ipybn` |
| **`src/`** | This is where our auxiliary scripts lies, code to scrap data, to convert stuff etc. | Small caps, no special character, `-` instead of spaces. |
| **`data/`** | This is not supposed to be committed, but it is where saved databases will be stored locally (scripts from `src/` should be able to get this data for you); a copy of this data will be available elsewhere (_just in case_). | Small caps, no special character, `-` instead of spaces. |

### Source files (`src/`)

Here we explain what each script from `src/` does for you:

##### One script to rule them all

1. `src/fetch_datasets.py` dowloads all the available datasets to `data/` is `.xz` compressed CSV format with headers translated to English.


##### Quota for Exercising Parliamentary Activity (CEAP)

1. `src/fetch_datasets.py --from-source` dowloads all CEAP datasets to `data/` from the official source (in XML format in Portuguese) .
1. `src/fetch_datasets.py` dowloads the CEAP datasets into `data/`; it can download them from the official source (in XML format in Portuguese) or from our backup server (`.xz` compressed CSV format, with headers translated to English).
1. `src/xml2csv.py` converts the original XML datasets to `.xz` compressed CSV format.
1. `src/translate_datasets.py` translates the datasets file names and the labels of the variables within these files.
1. `src/translation_table.py` creates a `data/YYYY-MM-DD-ceap-datasets.md` file with details of the meaning and of the translation of each variable from the _Quota for Exercising Parliamentary Activity_ datasets.

##### Suppliers information (CNPJ)

1. `src/fetch_cnpj_info.py` iterate over the CEAP datasets looking for supplier unique documents (CNPJ) and create a local dataset with each supplier info.
1. `src/clean_cnpj_info_dataset.py` clean up and translate the supplier info dataset.
1. `src/geocode_addresses.py` iterate over the supplier info dataset and add geolocation data to it (it uses the Google Maps API set in `config.ini`).

##### Miscellaneous
1. `src/backup_data.py` uploads files from `data/` to an Amazon S3 bucket set on `config.ini` .

### Datasets (`data/`)

Here we explain what are the datasets inside `data/`. They are not part of this repository, but downloaded with the scripts from `src/`. Most files are `.xz` compressed CSV.
All files are named with a [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) date suffix.

1. `data/YYYY-MM-DD-current-year.xz`, `data/YYYY-MM-DD-last-year.xz` and `data/YYYY-MM-DD-previous-years.xz`: Datasets from the _Quota for Exercising Parliamentary Activity_; for details on its variables and meaning, check `data/YYYY-MM-DD-ceap-datasets.md`.
1. `data/datasets-format.html`: Original HTML in Portuguese from the Chamber of Deputies explaining CEAP dataset variables.
1. `data/YYYY-MM-DD-ceap-datasets.md`: Table comparing contents from `data/YYYY-MM-DD-datasets_format.html` and our translation of variable names and descriptions.
1. `data/YYYY-MM-DD-companies.xz`: Dataset with suppliers info containing all the fields offered in the [Federal Revenue alternative API](http://receitaws.com.br) and complemented with geolocation (latitude and longitude) gathered from Google Maps.

## Four moments

The project basically happens in four moments, and contributions are welcomed in all of them:

| Moment | Description | Focus | Target |
|--------|-------------|-------|--------|
| **Possibilities** | To structure hypothesis and strategies taking into account (a) the source of the data, (b) how feasible it is to get this data, and (c) what is the purpose of bringing this data into the project.| Contributions here require more sagacity than technical skills.| [GitHub Issues](https://github.com/codelandev/serenata-de-amor/issues) |
| **Data collection** | Once one agrees that a certain _possibility_ is worth it, one might want to start writing code to get the data (this script's go into `src/`). | Technical skills in scrapping data and using APIs. | `src/` and `data/` |
| **Exploring** | Once data is ready to be used, one might want to start exploring and analyzing it. | Here what matters is mostly data science skills. | `develop/` |
| **Reporting** | Once a relevant finding emerge from the previous stages, this finding might be gathered with similar other findings (e.g. put together explorations on air tickets, car rentals and geolocation under a report on transportation) on a report. | Contributions here requires good communication skills and very basic understanding of quantitative methods. | `report/` |

## Jarbas

As soon as we started _Serenata de Amor_ [we felt the need for a simple webservice](https://github.com/datasciencebr/serenata-de-amor/issues/34) to browse our data and refer to documents we analize. This is how [Jarbas](https://github.com/datasciencebr/jarbas) was created.

If you fancy web development, feel free to check Jarba's source code, to check [Jarba's own Issues](https://github.com/datasciencebr/jarbas/issues) and to contribute there too.
