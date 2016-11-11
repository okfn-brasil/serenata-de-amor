
# coding: utf-8

# In[24]:

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# In[16]:

data = pd.read_csv('../data/2016-08-08-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# In[11]:

tot_deputado =    data.groupby(['party', 'state', 'applicant_id', 'congressperson_name'], as_index=False)   .aggregate({'net_value': np.sum})

tot_deputado.sort_values(by='net_value', ascending=False).head()


# In[ ]:




# In[21]:

tot_deputado =    data.groupby(['applicant_id', 'party', 'state', 'congressperson_name'])   .aggregate({'net_value': np.sum})

tot_deputado[200:250]


# In[36]:

tot = data.groupby(['subquota_number', 'subquota_description'], as_index=False)   .agg({'net_value': np.nansum})   .sort_values(by='net_value', ascending=False)

plt.xkcd()
plt.figure(figsize=(10,10))
plt.pie(tot.net_value, labels=tot.subquota_description)
plt.show()


# In[5]:

data.groupby(['cnpj_cpf', 'supplier'
             ], as_index=False)\
   .agg({'net_value': np.nansum})\
   .sort_values(by='net_value', ascending=False)[0:20]


# In[6]:

data.groupby(['subquota_group_id', 'subquota_group_description'], as_index=False)   .agg({'net_value': np.nansum})   .sort_values(by='net_value', ascending=False)[0:10]


# In[7]:

data.groupby(['year', 'month'], as_index=False)   .agg({'net_value': np.nansum})   .sort_values(by='month', ascending=True)[0:15]


# In[6]:

print('Type of receipt — 0 (zero) for bill of sale; 1 (one) for simple receipt; and 2 (two) to expense made abroad.')
data.groupby(['document_type'], as_index=False)   .agg({'net_value': np.nansum})   .sort_values(by='net_value', ascending=False).head()


# In[ ]:



