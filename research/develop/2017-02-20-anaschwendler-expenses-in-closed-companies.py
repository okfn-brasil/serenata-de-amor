
# coding: utf-8

# # Expenses in closed companies
# Recently we found out that there are many companies that are already closed or out of service, we are aiming to find if there are expenses made after the company situation as other than open.

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


# ## Formatting
# Formatting companies situation_date and reimbursements issue_date columns to correct date format (will be needed for a query later), and formatting the companies cpnj to a format without dash and dots.

# In[3]:

reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], errors='coerce')
companies['situation_date'] = pd.to_datetime(companies['situation_date'], errors='coerce')
companies['cnpj'] = companies['cnpj'].str.replace(r'\D', '')


# In[4]:

statuses = ['BAIXADA', 'NULA', 'SUSPENSA', 'INAPTA']
not_open = companies[companies['situation'].isin(statuses)]
not_open[['cnpj', 'situation_date','situation', 'situation_reason']].head(5)


# The column situation_date is the one that is interesting. Expenses made after that date should be considered suspicious.
# 
# The inner join on merge will give reimbursements that were requested for out of service companies.

# In[5]:

dataset = pd.merge(reimbursements, not_open, how='inner',
                   left_on='cnpj_cpf', right_on='cnpj')


# In[6]:

columns = ['congressperson_name', 'issue_date','cnpj', 'situation_date',
           'situation', 'situation_reason']
dataset[columns].head(10)


# In[7]:

dataset.shape


# In[8]:

dataset.iloc[0]


# ## Filtering suspicious reimbursements
# We have all reibursements requested for expenses made in companies that have situation other than "open".
# It is still necessary to check the reimbursement issue_date is "bigger" than the situation_date.

# In[9]:

expenses_in_closed_companies = dataset.query('issue_date > situation_date')
expenses_in_closed_companies[columns].head()


# In[10]:

expenses_in_closed_companies.shape


# We can safely say that there are 5222 suspicious reimbursements.
# For this analysis, I would like to thank @jtemporal for being my pair for all the coding, and helping me to understand the hypothesis.
