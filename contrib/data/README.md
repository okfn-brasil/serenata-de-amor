This directory contains sample data, useful if you just want to setup a developement environment.

This is **not** the full dataset.

These samples were created with a script like this (`pandas` and `numpy` required and **not** included in this repository):


```python
import re

import pandas as pd
import numpy as np


CSV_PARAMS = {
    'compression': 'xz',
    'encoding': 'utf-8',
    'index': False
}

# read all datasets
reimbursements = pd.read_csv('reimbursements.xz', dtype={ 'cnpj_cpf': np.str, 'reimbursement_numbers': np.str })
companies = pd.read_csv('companies.xz', dtype={ 'cnpj': np.str })
suspicions = pd.read_csv('suspicions.xz')

# get a sample of the reimbursements
sample = reimbursements.sample(1000)
sample.to_csv('reimbursements_sample.xz', **CSV_PARAMS)

# filter companies present in the sample
companies['cnpj_'] = companies.cnpj.apply(lambda x: re.sub(r'\D', '', x))
companies_sample = companies[companies.cnpj_.isin(sample.cnpj_cpf)]
del companies_sample['cnpj_']
companies_sample.to_csv('companies_sample.xz', **CSV_PARAMS)

# filter suspicions present in the sample
suspicions_sample = suspicions[suspicions.document_id.isin(sample.document_id)]
suspicions_sample.to_csv('suspicions_sample.xz', **CSV_PARAMS)
```
