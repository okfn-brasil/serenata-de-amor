
# coding: utf-8

# In[1]:

get_ipython().magic('matplotlib notebook')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[2]:

data = pd.read_csv('../data/2016-08-08-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# ### Reaching for subquota description

# In[7]:

list(data.columns.values)


# In[11]:

subquota_list = data['subquota_description'].unique()
print (subquota_list)


# In[13]:

len(subquota_list)


# ### End of subquota listings - WIP

# ### Checking net values from all the receipts

# In[14]:

data.net_value.describe()


# In[15]:

grouped = data.groupby('cnpj_cpf', as_index=False)

print('{} total cnpj/cpfs, {} are unique'.format(len(data), len(grouped)))


# ### Creating a dataframe with the first supplier name for each cnpj_cpf:
# 

# In[16]:

cnpj_cpfs = []
names = []
for group in grouped:
    cnpj_cpfs.append(group[0])
    names.append(group[1].iloc[0].supplier)

names = pd.DataFrame({'cnpj_cpf': cnpj_cpfs, 'supplier_name': names})
names.head()



# ### CNPJs/CPFs that received most payments 

# In[20]:

spent = grouped.agg({'net_value': np.nansum}).sort_values(by='net_value', ascending=False)

spent = pd.merge(spent, names, on='cnpj_cpf')
spent.head(10)


# # Stopying now - starting investigation for each micro-enterprise(ME) listed

# In[ ]:



