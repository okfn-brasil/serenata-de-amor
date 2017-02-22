
# coding: utf-8

# # Expenses in closed companies
# Recently we find out that there are many companies that are already closed, we are aiming to find if there is expenses made before the situation changed.

# In[1]:

import pandas as pd
import numpy as np
from serenata_toolbox.datasets import fetch

fetch('2016-09-03-companies.xz', '../data')
fetch('2016-11-19-reimbursements.xz', '../data')


# In[2]:

companies = pd.read_csv('../data/2016-09-03-companies.xz', low_memory=False)
reimbursements = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str},
                      low_memory=False)


# Setting companies situation_date and reimbursements issue_date columns to correct date format, and set the cpnj to a format without dash and dots.

# In[3]:

reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], errors='coerce')
reimbursements['issue_date'] = reimbursements['issue_date'].apply(lambda date: date.date())
companies['situation_date'] = pd.to_datetime(companies['situation_date'], errors='coerce')
companies['situation_date'] = companies['situation_date'].apply(lambda date: date.date())
companies['cnpj'] = companies['cnpj'].str.replace(r'\D', '')


# In[4]:

list(companies)[0:26]


# In[5]:

statuses = ['BAIXADA', 'NULA', 'SUSPENSA', 'INAPTA']
not_opened = companies[companies['situation'].isin(statuses)]
not_opened[['cnpj', 'situation_date','situation', 'situation_reason']].head(5)


# The column situation_date is the one that is interesting. Expenses made after that date should be considered suspicious.

# In[6]:

dataset = pd.merge(reimbursements, not_opened, how='inner',
                   left_on='cnpj_cpf', right_on='cnpj')


# In[7]:

columns = ['issue_date','cnpj', 'situation_date','situation', 'situation_reason']
dataset = dataset[columns]
dataset.head(10)


# The inner join on merge will give reimbursements that were requested for colsed companies. It is still necessary to check the reimbursement issue_date is "bigger" than the situation_date.

# In[8]:

dataset.iloc[0]


# In[12]:

expenses_in_closed_companies = dataset.query('issue_date > situation_date')
expenses_in_closed_companies.head()

