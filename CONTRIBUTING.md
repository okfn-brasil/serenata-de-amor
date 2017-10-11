# How to contribute?

## Before you start

If you work with statistics but are not a coder or a developer used to the routine below, or you are just willing to learn, share ideas and catch-up, join us in the [Telegram Open Group](http://bit.ly/2cUBFr6). This group keeps its language in English in order to be internationally open and we make Telegram the official channel to make it easy for non-developers to reach the technical group.


Also you should read [this article](https://datasciencebr.com/how-does-one-contribute-to-serenata-de-amor-operation-36e3e7b38207#.uoghp3dop), it explains how each part of Serenata de Amor works and how they all come together as whole. After reading it, you'll have a pretty good understanding of all the tools ([Jarbas](https://github.com/datasciencebr/jarbas), [Rosie](https://github.com/datasciencebr/rosie) and the [toolbox](https://github.com/datasciencebr/serenata-toolbox/)) that we use — we’ll refer to them below, so it’s nice to have an idea about what we’re talking about ;-)

## The basics

A lot of discussions about ideas take place in the [Issues](https://github.com/datasciencebr/serenata-de-amor/issues) section. There you can catch up with what's going on and also suggest new ideas.

1. _Fork_ this repository
2. Clone the repository: `git clone http://github.com/[YOUR_GITHUB_USER]/serenata-de-amor.git`
3. Create your branch: `$ git checkout -b new-stuff`
4. Commit your changes: `$ git commit -am 'My cool contribution'`
5. Push to the branch to your fork: `$ git push origin new-stuff`
6. Create a new _Pull Request_

## Environment

### Local Installation Environment (without Docker)

The recommended way of setting your environment up is with [Anaconda](https://www.continuum.io/), a Python distribution with useful packages for Data Science.

The project uses Python 3 (specified in the `python=3` bit of the commands below). [Download Anaconda](https://www.continuum.io/downloads) and create an _environment_ for the project.

You can use either Anaconda 2 and Anaconda 3, since `conda` environments manage Python versions. But if you're going to do a fresh install, we recommend Anaconda 3 — it's newer and it makes no sense to have Python 2 as your default Anaconda Python.

```console
$ cd serenata-de-amor
$ conda update conda
$ conda create --name serenata_de_amor python=3
$ source activate serenata_de_amor
$ ./setup
```

The `activate serenata_de_amor` command must be run every time you enter the project folder to start working.

**If you use Windows** skip the last two commands, run _Command Prompt_ as _Administrator_ and use:

```console
$ activate serenata_de_amor
$ python setup
```

#### Common (virtual) environment issues

In some environments Jupyter might not be able to access packages from the Conda environment (basically… for some reason). If this is the case we recommend you to ensure you are using Anaconda 4.1.0 or higher, delete the old environment and follow these steps:

```console
$ rm -rf ~/<path to your anaconda>/envs/serenata_de_amor
$ conda update conda
$ conda create --name serenata_de_amor python=3 ipykernel
$ source activate serenata_de_amor
$ conda install notebook ipykernel
$ ipython kernel install --user
$ conda install jupyter
$ ./setup
```

#### Pyenv users

If you installed Anaconda via [pyenv](https://github.com/yyuu/pyenv), `source activate serenata_de_amor` will probably fail _unless_ you explicitly use the path to the Anaconda `activate` script. For example:

```console
$ source /usr/local/var/pyenv/versions/anaconda3-4.1.1/bin/activate serenata_de_amor
```

### Docker Installation Environment

You can user [Docker](https://docs.docker.com/engine/installation/) and [Docker Compose](https://docs.docker.com/compose/install/) to have a working environment:

1. Create your `config.ini` file from the example: `$ cp config.ini.example config.ini`
1. Build the tags with `$ docker-compose build`
1. Start the environment (it might take a while, hurry not): `$ docker-compose up -d`.
1. You can start Jupyter Notebooks and access them at [localhost:8888](http://localhost:8888): `$ docker-compose run --service-ports research jupyter notebook`

If you want to access the console:

```console
$ docker-compose run --rm research bash
```

### Using Neo4j in graph analysis

[Neo4j](https://neo4j.com/) is a *graph* database that enables you analyse data expressing its relationship in a graph model.

If you plan to use Neo4j in your analysis and you don't have it installed, the easiest way to put it running is using `Docker`. If you prefer to install in a traditional way, please refer to Neo4j website for more information about [installation steps](https://neo4j.com/).

Please refer to `2017-02-12-marcusrehm-neo4j-guide` and `2017-02-12-marcusrehm-neo4j-example2` notebooks for more information on how to use it.

Neo4j integration in Jupyter notebooks is based on Nichole White's work. It can be found [here](https://github.com/nicolewhite/neo4j-jupyter).


## Best practices

In order to avoid tons of conflicts when trying to merge [Jupyter Notebooks](http://jupyter.org), there are some [guidelines we follow](http://www.svds.com/jupyter-notebook-best-practices-for-data-science/).

That said one of our best practices is creating a `.html` and a `.py` version of each notebook. This can be done automatically and painlessly by editing the config file `~/.jupyter/jupyter_notebook_config.py` and adding the folowing code:

```python
### If you want to auto-save .html and .py versions of your notebook:
# modified from: https://github.com/ipython/ipython/issues/8009
import os
from subprocess import check_call

def post_save(model, os_path, contents_manager):
    """post-save hook for converting notebooks to .py scripts"""
    if model['type'] != 'notebook':
        return # only do this for notebooks
    d, fname = os.path.split(os_path)
    check_call(['jupyter', 'nbconvert', '--to', 'script', fname], cwd=d)
    check_call(['jupyter', 'nbconvert', '--to', 'html', fname], cwd=d)

c.FileContentsManager.post_save_hook = post_save
```

Beyond that we have five big directories with different purposes:

| Directory | Purpose | File naming |
|-----------|---------|-------------|
| **`research/develop/`** | This is where we _explore_ data, feel free to create your own notebook for your exploration. | `[ISO 8601 date]-[author-username]-[2-4 word description].ipynb` (e.g. `2016-05-13-anaschwendler-air-tickets.ipynb`) |
|**`research/deliver/`** | This is where we write up the findings and results, here is where we put together different data, analysis and strategies to make a point, feel free to jump in. | Meaningful title for the report (e.g. `Transport-allowances.ipynb` |
| **`research/src/`** | This is where our auxiliary scripts lie: code to scrap data, to convert stuff, etc. | Small caps, no special character, `-` instead of spaces. |
| **`research/data/`** | This is not supposed to be committed, but it is where saved databases will be stored locally (scripts from `research/src/` should be able to get this data for you); a copy of this data will be available elsewhere (_just in case_). | Date prefix, small caps, no special character, `-` instead of spaces, preference for `.xz` compressed CSV (`YYYY-MM-DD-my-dataset.xz`). |
| **`docs/`** | Once a new subject, theme or dataset is added to project, would be nice to have some documentation describing these items and how others can use them. | Small caps whenever possible, no special character, `-` instead of spaces, preference for `.md` Markdown files. |  |

### The toolbox and our the source files (`research/src/`)

Here we explain what each script from `research/src/` and the `serenata_toolbox` do for you:

##### One toolbox to rule them all

With the [toolbox](https://github.com/datasciencebr/serenata-toolbox) you can download, translate and convert the dataset from XML to CSV. You can chec the [toolbox docs](http://serenata-toolbox.readthedocs.io/en/latest/) too.


When you run our setup, the toolbox is installed and all our datasets are downloaded to your `research/data/` directory. This is handled by these two single lines:
```python
from serenata_toolbox.datasets import fetch_latest_backup
fetch_latest_backup('data/')
```

##### Quota for Exercising Parliamentary Activity (CEAP)
1. `research/src/group_receipts.py` creates a `research/data/YYYY-MM-DD-reimbursements.xz` file with grouped data from all of the available datasets (`research/data/YYYY-MM-DD-current-year.xz`, `research/data/YYYY-MM-DD-last-year.xz` and `research/data/YYYY-MM-DD-previous-years.xz`)
1. `research/src/translation_table.py` creates a `research/data/YYYY-MM-DD-ceap-datasets.md` file with details of the meaning and of the translation of each variable from the _Quota for Exercising Parliamentary Activity_ datasets.


##### Suppliers information (CNPJ)
1. `research/src/fetch_cnpj_info.py` iterates over the CEAP datasets looking for supplier unique documents (CNPJ) and creates a local dataset with each supplier info, after that, cleans up and translates the dataset.
1. `research/src/geocode_addresses.py` iterates over the supplier info dataset and add geolocation data to it (it uses the Google Maps API set in `config.ini`).
1. `research/src/fetch_sex_places.py` fetches the closest sex related place (cat houses, night clubs, massage parlours etc.) to each company (use `--help` for further instructions).

##### Miscellaneous
1. `research/src/backup_data.py` uploads files from `research/data/` to an Amazon S3 bucket set on `config.ini` .

##### Politician's relatives
1. `research/src/get_family_names.py` gets the names of the parents of congresspeople from the congress website and saves them to `research/data/YYYY-MM-DD-congressperson_relatives.xz` (and it may save some data to `research/data/YYYY-MM-DD-congressperson_relatives_raw.xz` in case it fails to parse the names)

##### Deputies Advisors
1. `research/src/fetch_deputies_advisors.py` gets the name and point number (and act's issued place and date when available) of all advisors of current deputies from Chamber of Deputies website and saves to `research/data/YYYY-MM-DD-deputies-advisors.xz`

##### Federal Budget
1. `research/src/fetch_federal_budget_datasets.py` downloads datasets files of agreements made with Federal Budget and their related amendments.  The script gets the lastest version available for each dataset, unpacks, translates columns to english and saves them into `research/data/`. The files are named as follows:
 - Agreements:  `YYYY-MM-DD-agreements.xz`
 - Amendments: `YYYY-MM-DD-amendments.xz`

##### Electoral information
1. `research/src/fetch_tse_data.py` downloads datasets files from TSE website and organize them in the dataset `research/data/YYYY-MM-DD-tse-candidates.xz`.

##### Companies and Non-Profit Entities with sanctions (CEIS, CEPIM and CNEP).
1. `research/src/fetch_federal_sanctions.py` downloads all three datasets files (CEIS, CEPIM and CNEP) from official source. The script gets the lastest version available for each dataset, unpacks, translates columns to english and saves them into `research/data/`. The files are named as follows:
 - CEIS: `YYYY-MM-DD-inident-and-suspended-companies.xz`
 - CEPIM: `YYYY-MM-DD-impeded-non-profit-entities.xz`
 - CNEP: `YYYY-MM-DD-national-register-punished-companies.xz`

##### Purchase suppliers
1. `research/src/fetch_purchase_suppliers.py` collects the data of all suppliers related with purchases made by federal government. The purchases could be by a company or by a person. The file is named as follows: `YYYY-MM-DD-purchase-suppliers.xz`.

##### Congresspeople details
1. `research/src/fetch_congressperson_details.py` collects personal details (civil name, birth date and gender) from congresspeople. The file is named as follows: `YYYY-MM-DD-congressperson-details.xz`.

#### Brazilian cities
1. `research/src/grequests_transparency_portal_cities.py` generates a dataset containing all available
links for transparency portal from each Brazilian city that already have them. The output file can be found at `research/data/` and is named as follows: `YYYY-MM-DD-cities-with-tp-url.xz`.

### Datasets (`research/data/`)

Here we explain what are the datasets inside `research/data/`. They are not part of this repository, but can be downloaded with the [toolbox](https://github.com/datasciencebr/serenata-toolbox). Most files are `.xz` compressed CSV.
All files are named with a [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) date suffix.

1. `research/data/YYYY-MM-DD-current-year.xz`, `research/data/YYYY-MM-DD-last-year.xz` and `research/data/YYYY-MM-DD-previous-years.xz`: Datasets from the _Quota for Exercising Parliamentary Activity_; for details on its variables and meaning, check `research/data/YYYY-MM-DD-ceap-datasets.md`.
1. `research/data/datasets-format.html`: Original HTML in Portuguese from the Chamber of Deputies explaining CEAP dataset variables.
1. `research/data/YYYY-MM-DD-ceap-datasets.md`: Table comparing contents from `data/YYYY-MM-DD-datasets_format.html` and our translation of variable names and descriptions.
1. `research/data/YYYY-MM-DD-companies.xz`: Dataset with suppliers info containing all the fields offered in the [Federal Revenue alternative API](http://receitaws.com.br) and complemented with geolocation (latitude and longitude) gathered from Google Maps.
1. `research/data/YYYY-MM-DD-congressperson_relatives.xz` contains data on the relatives of congresspeople and the nature of their relationship.
1. `research/data/YYYY-MM-DD-congressperson_relatives_raw.xz` also contains data on the relatives of congresspeople, but is only created if `research/src/get_family_names.py` fails to handle some names.
1. `research/data/YYYY-MM-DD-deputies-advisors.xz` contains data from advisors of each deputy in the current term along with the deputy number and deputy name.
1. `research/data/YYYY-MM-DD-sex-place-distances` contains data from the closest sex related place (cat houses, night clubs, massage parlours etc.) to each company (including distance in meters) — this dataset is just a sample (check [this notebook](research/develop/2017-04-21-cuducos-explore-sex-places-dataset.ipynb) for details).
1. `research/data/YYYY-MM-DD-tse-candidates.xz` contains information about politicians candidacy over the last years. Can be used to extract a list of all politicians in Brazil.
1. `research/data/YYYY-MM-DD-congressperson-details.xz` contains the birth date, gender and civil name of congresspeople.
1. `research/data/YYYY-MM-DD-brazilian-cities.csv` contains information about all Brazilian cities (e.g. city code, state and name).
1. `research/data/YYYY-MM-DD-receipts-texts.xz` OCR of nearly 200k reimbursement receipts using Google's Cloud Vision API, for more information see the documentation on [docs/receipts-ocr.md](docs/receipts-ocr.md)


## Four moments

The project basically happens in four moments, and contributions are welcomed in all of them:

| Moment | Description | Focus | Target |
|--------|-------------|-------|--------|
| **Possibilities** | To structure hypotheses and strategies taking into account (a) the source of the data, (b) how feasible it is to get this data, and (c) what is the purpose of bringing this data into the project.| Contributions here require more sagacity than technical skills.| [GitHub Issues](https://github.com/codelandev/serenata-de-amor/issues) |
| **Data collection** | Once one agrees that a certain _possibility_ is worth it, one might want to start writing code to get the data (these scripts go into `research/src/`). | Technical skills in scrapping data and using APIs. | `research/src/`, `research/data/` and `docs/` |
| **Exploring** | Once data is ready to be used, one might want to start exploring and analyzing it. | Here what matters is mostly data science skills. | `research/develop/` |
| **Reporting** | Once a relevant finding emerges from the previous stages, this finding might be gathered with other similar findings (e.g. put together explorations on airline tickets, car rentals and geolocation under a report on transportation) on a report. | Contributions here require good communication skills and very basic understanding of quantitative methods. | `research/report/` |

## More about the Quota for Exercising Parliamentary Activity (CEAP)

If you read Portuguese there is [the official page](http://www2.camara.leg.br/participe/fale-conosco/perguntas-frequentes/cota-para-o-exercicio-da-atividade-parlamentar) with the legal pieces defining the quota and also [a human version of the main text](docs/CEAP.md) we made.

Also you can find more about the dataset variables [in Jarbas](http://jarbas.datasciencebr.com/static/ceap-datasets.html) or in `research/data/YYYY-MM-DD-ceap-datasets.md` that was downloaded when you [ran the setup](#one-toolbox-to-rule-them-all).

## More about Federal Budget

As a secondary goal, some datasets related to Federal Budget and its uses were analyzed crossing them with datasets of inident and suspect companies that have suffered some sanction by Federal Government and are suspended from entering into any type of contract with Federal Government during sactions.

It is a work in progress as other datasets can be downloaded from [SICONV](http://portal.convenios.gov.br/download-de-dados) and documentation can also be improved.

You can read more about these datasets at:
- [federal-budget-agreements-datasets.md](docs/federal-budget-agreements-datasets.md)
- [companies-with-federal-sanctions-datasets.md](docs/companies-with-federal-sanctions-datasets.md)

The notebook with the analysis are:
- 2016-12-12-marcusrehm-federal-budget-companies-with-sanctions.ipynb
- 2017-01-15-marcusrehm-congressperson-reimbursements-from-companies-with-sanctions.ipynb
