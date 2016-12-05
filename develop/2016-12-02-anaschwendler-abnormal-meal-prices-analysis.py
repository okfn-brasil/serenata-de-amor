
# coding: utf-8

# # Detecting abnormal meal prices

# There's a list of meal reimbursements made using the CEAP. We want to alert about anomalies found in this dataset based on known information about food expenses.

# In[1]:

get_ipython().magic('matplotlib notebook')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[2]:

reimbursements = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                      dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str},
                      low_memory=False)


# In[3]:

reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], errors='coerce')
reimbursements.sort_values('issue_date', inplace=True)


# ## Data preparation

# In[4]:

meals = reimbursements[reimbursements.subquota_description == 'Congressperson meal']
meals.head()


# In[5]:

meals.total_net_value.describe()


# In[11]:

meals = meals[meals['congressperson_id'].notnull()]
meals.shape


# In[13]:

grouped = meals.groupby('cnpj_cpf', as_index=False)
print('{} total cnpj/cpfs, {} are unique'.format(len(meals), len(grouped)))


# In[14]:

cnpj_cpfs = []
names = []
for group in grouped:
    cnpj_cpfs.append(group[0])
    names.append(group[1].iloc[0].supplier)

names = pd.DataFrame({'cnpj_cpf': cnpj_cpfs, 'supplier_name': names})
names.head()


# In[10]:

keys = ['congressperson_name', 'issue_date']
aggregation = meals.groupby(keys)['total_net_value'].     agg({'sum': np.sum, 'expenses': len, 'mean': np.mean})


# In[8]:

aggregation.sort_values(['expenses', 'sum'], ascending=[False, False]).head(10)

