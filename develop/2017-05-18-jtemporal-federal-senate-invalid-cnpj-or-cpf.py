
# coding: utf-8

# # Invalid CNPJ or CPF
# 
# `cnpj_cpf` is the column identifying the company or individual who received the payment made by the congressperson. Having this value empty should mean that it's an expense made outside Brazil, with a company (or person) without a Brazilian ID.

# In[1]:

import numpy as np
import pandas as pd

dataset = pd.read_csv('../data/2017-05-17-federal-senate-reimbursements.xz',                      dtype={'cnpj_cpf': np.str}, encoding = "utf-8")


# In[2]:

dataset = dataset[dataset['cnpj_cpf'].notnull()]
dataset


# In[3]:

from pycpfcnpj import cpfcnpj

def validate_cnpj_cpf(cnpj_or_cpf):
    return (cnpj_or_cpf == None) | cpfcnpj.validate(cnpj_or_cpf)



cnpj_cpf_list = dataset['cnpj_cpf'].astype(np.str).replace('nan', None)
dataset['valid_cnpj_cpf'] = np.vectorize(validate_cnpj_cpf)(cnpj_cpf_list)


# In[4]:

dataset.query('valid_cnpj_cpf != True').head()


# So, this proves that we can find reimbursements without valid `cnpj_cpf`.
# 
# Plus, we need to add a `document_type` to the dataset to fit in the core module.

# In[5]:

dataset['document_type'] = 'simple_receipt'
dataset

