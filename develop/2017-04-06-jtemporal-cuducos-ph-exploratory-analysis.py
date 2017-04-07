
# coding: utf-8

# # Piaui Herald - Exploratory Data Analysis
# Finding interesting cases for Rosie's column

# In[1]:

import numpy as np
import pandas as pd

dataset = pd.read_csv('../../../serenata-data/2017-03-15-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str,
                             'document_id': np.int},
                      low_memory=False)


# ## Luxury Hotel

# In[2]:

lodging = dataset[dataset['subquota_description'] == 'Lodging, except for congressperson from Distrito Federal']
keys = ['congressperson_id','cnpj_cpf', 'supplier']
grouped = lodging.groupby(keys)


# Number of Lodging expenses

# In[3]:

len(grouped)


# In[4]:

subquota_numbers = grouped['subquota_number'].agg(lambda x: ','.join(x)).reset_index()
subquota_numbers.head()


# In[5]:

document_ids = grouped['document_id'].agg(lambda x: tuple(x)).reset_index()
document_ids.head()


# In[6]:

net_values_sum = grouped['total_net_value'].agg({'sum': np.sum}).reset_index()
net_values_sum.head()


# In[7]:

aggregation = pd.merge(pd.merge(subquota_numbers, document_ids, on=keys),
                       net_values_sum, on=keys)
aggregation.head()


# Get net value by row

# In[8]:

def get_top_net_value(row):
    l = list(row['document_id'])
    values = []
    for reimbursement_id in l:
        values.append(float(dataset[dataset['document_id'] == reimbursement_id]['total_net_value']))
    return {'top_net_value':max(values), 'top_document':l[values.index(max(values))]}


# In[9]:

top_things = aggregation.apply(func=get_top_net_value, axis='columns')
# new columns
aggregation['top_net_value'], aggregation['top_document'] = "",""


# In[10]:

for _ in range(len(top_things)):
    # paliative since DataFrame.replace() did not work ¯\_(ツ)_/¯
    aggregation.loc[_, 'top_net_value'] = top_things[_]['top_net_value']
    aggregation.loc[_, 'top_document'] = top_things[_]['top_document']


# In[11]:

aggregation.head()


# In[12]:

aggregation = aggregation.sort_values(by='top_net_value', ascending=False)
aggregation.head(10)

