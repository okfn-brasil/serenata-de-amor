# Rosie, the robot

A Python application reading receipts from the Quota for Exercising Parliamentary Activity (aka CEAP, from the Brazilian Chamber of Deputies) and outputs, for each of the receipts, a "probability of corruption" and a list of reasons why is considered this way.

- [x] Fetch CEAP dataset from Chamber of Deputies
- [x] Convert XML to CSV
- [x] Translate CSVs to English
- [ ] Read CEAP dataset from CSV into Pandas
- [ ] Process in the "corruption pipeline"
    - [ ] Monthly limits (quota and subquota)
    - [ ] Machine Learning models using scikit-learn
- [ ] Task to push to Jarbas via API


```python
import os
from serenata_toolbox.ceap_dataset import CEAPDataset

path = '/tmp/serenata-data'
path = 'data'
os.makedirs(path, exist_ok=True)
ceap = CEAPDataset(path)
ceap.fetch()
ceap.convert_to_csv()
ceap.translate()
ceap.clean()
```

## Setup

```console
$ cd rosie
$ conda update conda
$ conda create --name serenata_rosie python=3
$ source activate serenata_rosie
$ ./setup
```
