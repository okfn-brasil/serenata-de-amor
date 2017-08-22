
# coding: utf-8

# # Invalid CNPJ or CPF from Federal Senate CEAP
# 
# `cnpj_cpf` is the column identifying the company or individual who received the payment made by the congressperson. Having this value empty should mean that it's an expense made outside Brazil, with a company (or person) without a Brazilian ID.

# In[1]:

import numpy as np
import pandas as pd

from serenata_toolbox.datasets import fetch

fetch('2017-05-22-federal-senate-reimbursements.xz', '../data/')


# In[2]:

dataset = pd.read_csv('../data/2017-05-22-federal-senate-reimbursements.xz',                      converters={'cnpj_cpf': np.str}, encoding = 'utf-8')


# In[3]:

dataset = dataset[dataset['cnpj_cpf'].notnull()]
dataset.head()


# In[4]:

from pycpfcnpj import cpfcnpj

def validate_cnpj_cpf(cnpj_or_cpf):
    return (cnpj_or_cpf == None) | cpfcnpj.validate(cnpj_or_cpf)



cnpj_cpf_list = dataset['cnpj_cpf'].astype(np.str).replace('nan', None)
dataset['valid_cnpj_cpf'] = np.vectorize(validate_cnpj_cpf)(cnpj_cpf_list)


# In[5]:

dataset.query('valid_cnpj_cpf != True').head()


# So, this proves that we can find reimbursements without valid `cnpj_cpf`.
# 
# Plus, we need to add a `document_type` to the dataset to fit in the core module.

# In[6]:

dataset['document_type'] = 'unknown'
dataset.iloc[0]

