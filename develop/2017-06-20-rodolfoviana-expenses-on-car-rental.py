
# coding: utf-8

# ## Expenses on car rental
# 
# This analysis aims to investigate expenses on car rental during the current term. Previous analysis I did using Excel shows 1) some politicians systematically spends above the monthly limit of R$ 10K, and 2) some congresspersons rent more than one vehicle every month, which brings certain suspicion: considering they work in DF, are those cars rented outside DF being used by someone else? 
# 
# ~~**First step:** get a list of congresspersons, the amount reimbursed by them since Jan. 2015 and the dates of those reimbursements. Then we cross these data with the list of companies that rented those vehicles so we can get information on where those rentals occurred.~~ *Done!*
# 
# **Second step:** get datasets (sessions, speeches) that may prove whether congressperson was or was not in DF in specific periods of time: when the vehicles were rented. So we can get, as a result, months in which the congressperson spent most of his/her time in DF, but payed a full-month rent somewhere else. *I need some help here.*
# 
# -- Rodolfo Viana

# In[1]:

import pandas as pd
import numpy as np

data = pd.read_csv('../data/2017-06-04-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'congressperson_name': np.str,
                             'subquota_number': np.str,
                             'issue_date': np.str,
                             'document_id': np.str},
                      low_memory=False)


# #### Selecting term, subquota
# 
# There are 14,263 reimbursements since Jan. 2015. They sum up to R$ 60,373,960.80.

# In[2]:

data = data[data['year'] >= 2015]
data = data[data['subquota_description'] == 'Automotive vehicle renting or charter']
data['cnpj_cpf'] = data['cnpj_cpf'].str.replace(r'[\.\/\-]', '')
data.subquota_description.value_counts()


# In[3]:

data.net_values.sum()


# In[4]:

congressperson_list = data[['congressperson_name', 
                            'congressperson_id', 
                            'net_values', 
                            'month', 
                            'year', 
                            'issue_date', 
                            'document_id',
                            'cnpj_cpf']]


# In[5]:

congressperson_expenses = congressperson_list.groupby(['congressperson_name', 
                                                       'year', 
                                                       'month', 
                                                       'issue_date', 
                                                       'document_id']).agg({'net_values':sum})

congressperson_expenses.head(20)


# #### Getting companies dataset, excluding those from DF, merging with reimbursements dataset
# 
# There are 10,945 companies outside DF. The receipts sum up to R$ 49,156,001.56.

# In[6]:

companies = pd.read_csv('../data/2017-05-21-companies-no-geolocation.xz', low_memory=False)
companies = companies[companies['state'] != 'DF']
companies['cnpj'] = companies['cnpj'].str.replace(r'[\.\/\-]', '')


# In[7]:

dataset = pd.merge(data, companies, how='inner',
                   left_on='cnpj_cpf', right_on='cnpj')


# In[8]:

congressperson_expenses_dataset = dataset.groupby(['congressperson_name', 
                                                    'year', 
                                                    'month', 
                                                    'issue_date',
                                                    'cnpj',
                                                    'name',
                                                    'city',
                                                    'state_y',
                                                    'document_id']).agg({'net_values':sum})
full_report = congressperson_expenses_dataset.reset_index()


# In[9]:

full_report.name.count()


# In[10]:

full_report.net_values.sum()


# #### Getting outliers
# 
# Although Rosie considers mean value + three times the std value to point outliers, here we consider mean value + twice the std value. This is due to the subquota category -- different from other categoris (i.e. taxi, food, hotel), big money is spent on car rental, and work with 3 x std value would let suspect receipts pass.

# In[11]:

full_report.net_values.describe()


# In[12]:

outliers = full_report[full_report['net_values'] >= (full_report.net_values.mean() + (2 * full_report.net_values.std()))].sort_values('net_values', ascending=False)


# In[13]:

outliers.congressperson_name.value_counts().head(20)


# In[14]:

outliers.net_values.sum()


# ### Conclusion (so far)
# 
# In the current term (since Jan. 2015), congresspersons have reimbursed R$ 49,156,001.56 due to expenses on car rental outside DF. We have here vehicles rented for few days, which is something normal, and possibly cars rented for the whole month --and this is unusual, considering congresspersons work in DF.
# 
# As I am newbie at statistics, I considered the sum of mean value and twice the standard value to point outliers --or should I consider any other? The outliers sum up to R$ 8,712,789.41.
# 
# Now I need help to go on with the second step and some review of the first step, so I can figure out how to improve this analysis. 
# 
# This analysis will be updated soon.
