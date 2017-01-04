
# coding: utf-8

# # Look for companies with congresspeople names
# 
# Sometimes the trade company name is the owner's name, specially when it has just a single parter. Searching for these companies (possibly filtering by legal_entity equals to 213-5 - EMPRESARIO (INDIVIDUAL)) may bring good results.

# In[15]:

from serenata_toolbox.datasets import fetch

fetch('2016-12-06-reimbursements.xz', '../data')
fetch('2016-12-06-companies.xz', '../data')
fetch('2016-12-21-deputies.xz', '../data')


# In[5]:

import numpy as np
import pandas as pd

reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz',
                             dtype={'cnpj_cpf': np.str},
                             low_memory=False)


# In[10]:

reimbursements['supplier'].unique()


# In[14]:

reimbursements['congressperson_name'].unique()


# In[19]:

deputies = pd.read_csv('../data/2016-12-21-deputies.xz',
                       usecols=['congressperson_id', 'civil_name'])
deputies.head()


# In[31]:

supplier_has_congressperson_name =     reimbursements['supplier'].isin(deputies['civil_name'])
reimbursements.loc[supplier_has_congressperson_name,
                   ['issue_date', 'congressperson_name', 'supplier', 'subquota_description', 'cnpj_cpf', 'document_id', 'total_net_value']]


# In[ ]:



