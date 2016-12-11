
# coding: utf-8

# # Invalid CNPJ or CPF
# 
# `cnpj_cpf` is the column identifying the company or individual who received the payment made by the congressperson. Having this value empty should mean that it's an expense made outside Brazil, with a company (or person) without a Brazilian ID.

# In[1]:

import numpy as np
import pandas as pd

dataset = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str},
                      low_memory=False)
dataset.shape


# In[2]:

from pycpfcnpj import cpfcnpj

def validate_cnpj_cpf(cnpj_or_cpf):
    return (cnpj_or_cpf == None) | cpfcnpj.validate(cnpj_or_cpf)



cnpj_cpf_list = dataset['cnpj_cpf'].astype(np.str).replace('nan', None)
dataset['valid_cnpj_cpf'] = np.vectorize(validate_cnpj_cpf)(cnpj_cpf_list)


# `document_type` 2 means expenses made abroad.

# In[3]:

keys = ['year',
        'applicant_id',
        'document_id',
        'total_net_value',
        'cnpj_cpf',
        'supplier',
        'document_type']
dataset.query('document_type != 2').loc[~dataset['valid_cnpj_cpf'], keys]


# With 1,532,491 records in the dataset and just 10 with invalid CNPJ/CPF, we can probably assume that the Chamber of Deputies has a validation in the tool where the congressperson requests for reimbursements. These represent a mistake in the implemented algorithm.

# In[ ]:



