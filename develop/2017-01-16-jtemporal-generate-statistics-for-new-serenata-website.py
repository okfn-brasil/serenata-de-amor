
# coding: utf-8

# # Generate statistics to be used on the new Serenata website
# 
# Now in the end of the project we need some statistics for the new website.
# 

# In[3]:

import numpy as np
import pandas as pd

dataset = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str},
                      low_memory=False)


# We will need formated data for the analysis down the road:

# In[4]:

dataset['issue_date'] = pd.to_datetime(dataset['issue_date'], errors='coerce')
dataset['issue_date_day'] = dataset['issue_date'].apply(lambda date: date.day)
dataset['issue_date_month'] = dataset['issue_date'].apply(lambda date: date.month)
dataset['issue_date_year'] = dataset['issue_date'].apply(lambda date: date.year)
dataset['issue_date_weekday'] = dataset['issue_date'].apply(lambda date: date.weekday())
dataset['issue_date_week'] = dataset['issue_date'].apply(lambda date: date.week)


# ## Total spent in one year
# 
# We want to see how much was spent in reimbursements in one year.
# The dataset goes from 2009 to 2016.

# In[3]:

years = [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016]
for i in years:
    print(i, ': ', sum(dataset[dataset['issue_date_year'] == i]['total_net_value']))


# And the average considering all eight years:

# In[4]:

sum(dataset['total_net_value']) / 8


# Would be nice to know on average how much is spent in one day of reibursments for one congress person

# In[5]:

keys = ['congressperson_name', 'issue_date']                                    
aggregation = dataset.groupby(keys)['total_net_value'].             agg({'sum': np.sum, 'expenses': len, 'median': np.median})
aggregation['expenses'] = aggregation['expenses'].astype(np.int)
print(aggregation['median'].median())


# ## Some subquotas
# ### Meals

# In[7]:

meals_dataset = dataset[dataset['subquota_description'] == 'Congressperson meal']
meals_dataset.shape


# In[8]:

meals_dataset.head()


# I want to find which was the highest value reimbursed to a congress person
# for one meal

# In[9]:

max(meals_dataset['total_net_value'])


# Now let's check what was top meal reibursments made in one day
# highest number of meals reibursments in one day

# In[11]:

keys = ['congressperson_name', 'issue_date']
meals_aggregation = meals_dataset.groupby(keys)['total_net_value'].agg({'sum': np.sum, 'expenses': len, 'mean': np.mean})
meals_aggregation['expenses'] = meals_aggregation['expenses'].astype(np.int)
meals_aggregation.sort_values(['expenses', 'sum'], ascending=[False, False]).head(10)
max(meals_aggregation['expenses'])


# ## Other sub-quotas
# Not all sub-quotas have an ceiling (e.g.: Congressperson Meal), considering these four that have,
# how many congress people use the whole sub-quota monthly

# In[13]:

SUB_QUOTAS = {
        'Fuels and lubricants': 6000,
        'Automotive vehicle renting or charter': 10900,
        'Taxi, toll and parking': 2700,
        'Security service provided by specialized company': 8700,
}

keys = ['congressperson_name', 'issue_date_month', 'issue_date_year']
for i in SUB_QUOTAS:
    subquotas = dataset
    subquotas = subquotas[subquotas['subquota_description'] == i]
    subquotas_agg = subquotas.groupby(keys)['total_net_value'].agg({'sum': np.sum, 'expenses': len, 'mean': np.mean})              
    subquotas_agg['expenses'] = subquotas_agg['expenses'].astype(np.int)
    subquotas_agg = subquotas_agg[subquotas_agg['sum'] == SUB_QUOTAS[i]]
    print(i, len(set(list(subquotas_agg.index.get_level_values(0)))))


# In[ ]:



