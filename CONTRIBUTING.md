# How to contribute?

## The basic

A lot of discussions about ideas take place in the [Issues](https://github.com/datasciencebr/serenata-de-amor/issues) section. There you can catch up with what's going on and also suggest new ideas.

1. _Fork_ this repository
2. Create your branch: `$ git checkout -b xx-new-stuff` where `xx` are your initials (e.g `jd` for John Doe)
3. Commit your changes: `$ git commit -am 'My cool contribution'`
4. Push to the branch to your fork: `$ git push origin xx-new-stuff`
5. Create a new _Pull Requesthttps://github.com/datasciencebr/jarbas/issues_

## Environment

The recommended way of setting your environment up is with [Anaconda](https://www.continuum.io/), a Python distribution with useful packages for Data Science. [Download it](https://www.continuum.io/downloads) and create an _environment_ for the project.

```console
$ conda update conda
$ conda create --name serenata_de_amor python=3
$ source activate serenata_de_amor
$ ./setup
```

The `activate serenata_de_amor` command must be run every time you enter in the project folder to start working.

## Best practices

In order to avoid tons of conflicts when trying to merge [Jupyter Notebooks](http://jupyter.org), there are some [guidelines we follow](http://www.svds.com/jupyter-notebook-best-practices-for-data-science/).

Basically we have four big directories with different purposes:

| Directory | Purpose | File naming |
|-----------|---------|-------------|
| **`develop/`** | This is where we _explore_ data, feel free to create your own notebook for your exploration. | `[ISO 8601 date]-[author-initials]-[2-4 word description].ipynb` (e.g. `2016-05-13-ec-air-tickets.ipynb`) |
|**`report/`** | This is where we write up the findings and results, here is where we put together different data, analysis and strategies to make a point, feel free to jump in. | Meaninful title for the report (e.g. `Transport-allowances.ipybn` |
| **`src/`** | This is where our auxiliary scripts lies, code to scrap data, to convert stuff etc. | Small caps, no special character, `-` instead of spaces. |
| **`data/`** | This is not suppose to be committed, but it is where saved databases will be stored locally (scripts from `src/` should be able to get this data for you); a copy of this data will be available elsewhere (_just in case_). | Small caps, no special character, `-` instead of spaces. |


## Four moments

The project basically happens in four moments, and contributions are welcomed in all of them:

| Moment | Description | Focus | Target |
|--------|-------------|-------|--------|
| **Possibilities** | To structure hypothesis and strategies taking into account (a) the source of the data, (b) how feasible it is to get this data, and (c) what is the purpose of bringing this data into the project.| Contributions here require more sagacity than technical skills.| [GitHub Issues](https://github.com/codelandev/serenata-de-amor/issues) |
| **Data collection** | Once one agrees that a certain _possibility_ is worth it, one might want to start writing code to get the data (this script's go into `src/`). | Technical skills in scrapping data and using APIs. | `src/` and `data/` |
| **Exploring** | Once data is ready to be used, one might want to start explore and analyze it. | Here what matters is mostly data science skills. | `develop/` |
| **Reporting** | Once a relevante finding emerge from the previous stages, this finding might be gathered with similar other findings (e.g. put together explorations on air tickets, car rentals and geolocation under a report on transportation) on a report. | Contributions here requires good communication skills and very basic understanding of quantitative methods. | `report/` |
