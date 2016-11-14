
# coding: utf-8

# # Doublechecking net values
# 
# Some people have been reporting problems in the value of `net_value` column in the CEAP datasets. It doesn't seem to really match what it should contain.

# In[1]:

import pandas as pd
import numpy as np

filenames = ['../data/2016-08-08-current-year.xz',
             '../data/2016-08-08-last-year.xz',
             '../data/2016-08-08-previous-years.xz']
dataset = pd.DataFrame()

for filename in filenames:
    data = pd.read_csv(filename,
                       parse_dates=[16],
                       dtype={'document_id': np.str,
                              'congressperson_id': np.str,
                              'congressperson_document': np.str,
                              'term_id': np.str,
                              'cnpj_cpf': np.str,
                              'reimbursement_number': np.str})
    dataset = pd.concat([dataset, data])


# In[2]:

dataset['issue_date'] = pd.to_datetime(dataset['issue_date'], errors='coerce')


# In[3]:

(dataset['document_value'].isnull()).sum()


# In[4]:

dataset[dataset['document_value'].isnull()]


# In[5]:

dataset[dataset['document_value'].isnull()].iloc[0]


# In[6]:

import math

dataset = dataset.dropna(subset=['document_value'])
dataset['document_value_int'] = (dataset['document_value'] * 100.).apply(math.ceil).astype(np.int)
dataset['remark_value_int'] = (dataset['remark_value'] * 100.).apply(math.ceil).astype(np.int)
dataset['net_value_int'] = (dataset['net_value'] * 100.).apply(math.ceil).astype(np.int)
dataset['calc_net_value_int'] = dataset['document_value_int'] - dataset['remark_value_int']


# In[7]:

((dataset['calc_net_value_int'] - dataset['net_value_int']) != 0).sum()


# In[8]:

dataset.iloc[0]


# In[9]:

dataset['diff_net_value'] = dataset['calc_net_value_int'] - dataset['net_value_int']
dataset.loc[dataset['diff_net_value'] != 0, 'diff_net_value'].describe()


# In[10]:

with_significant_difference = dataset.loc[dataset['diff_net_value'].abs() > 2]


# In[11]:

with_significant_difference['subquota_description'].describe()


# In[12]:

from altair import *

Chart(with_significant_difference).mark_bar().encode(
    x=X('subquota_description:O',
        sort=SortField(field='subquota_description',
                       order='descending',
                       op='count')),
    y='count(*):Q',
)


# In[13]:

with_significant_difference.iloc[0]


# In[ ]:



