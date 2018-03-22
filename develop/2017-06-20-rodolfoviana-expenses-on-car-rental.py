
# coding: utf-8

# ## Expenses on car rental
# 
# This analysis aims to investigate expenses on car rental during the current term. Previous analysis I did using Excel shows 1) some politicians systematically spends above the monthly limit of R$ 10K, and 2) some congresspersons rent more than one vehicle every month, which brings certain suspicion: considering they work in DF, are those cars rented outside DF being used by someone else? 
# 
# ~~**First step:** get a list of congresspersons, the amount reimbursed by them since Jan. 2015 and the dates of those reimbursements. Then we cross these data with the list of companies that rented those vehicles so we can get information on where those rentals occurred.~~ *Done!*
# 
# **Second step:** get expenses on toll to check whether those cars left the origin city or not. *In development.*
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
data['cnpj_cpf'] = data['cnpj_cpf'].str.replace(r'[\.\/\-]', '')
data_car = data[data['subquota_description'] == 'Automotive vehicle renting or charter']
data_car.subquota_description.value_counts()


# In[3]:

data_car.net_values.sum()


# In[4]:

congressperson_list_car = data_car[['congressperson_name', 
                            'congressperson_id', 
                            'net_values', 
                            'month', 
                            'year', 
                            'issue_date', 
                            'document_id',
                            'cnpj_cpf']]


# In[5]:

congressperson_expenses_car = congressperson_list_car.groupby(['congressperson_name', 
                                                               'year', 
                                                               'month', 
                                                               'issue_date', 
                                                               'document_id']).agg({'net_values':sum})

congressperson_expenses_car.head(20)


# #### Getting companies dataset, excluding those from DF, merging with reimbursements dataset
# 
# There are 10,945 companies outside DF. The receipts sum up to R$ 49,156,001.56.

# In[6]:

companies = pd.read_csv('../data/2017-05-21-companies-no-geolocation.xz', low_memory=False)
companies['cnpj'] = companies['cnpj'].str.replace(r'[\.\/\-]', '')
companies_cars = companies[companies['state'] != 'DF']


# In[7]:

dataset_car = pd.merge(data_car, companies_cars, how='outer',
                   left_on='cnpj_cpf', right_on='cnpj')


# In[8]:

congressperson_expenses_dataset_car = dataset_car.groupby(['congressperson_name',
                                                    'applicant_id',
                                                    'year', 
                                                    'month', 
                                                    'issue_date',
                                                    'cnpj',
                                                    'name',
                                                    'city',
                                                    'state_y',
                                                    'document_id']).agg({'net_values':sum})
full_report_car = congressperson_expenses_dataset_car.reset_index()


# In[9]:

full_report_car.name.count()


# In[10]:

full_report_car.net_values.sum()


# #### Getting outliers
# 
# #### On x times `std value` and threshold
# 
# As I am not familiar with statistics, I tested 2 x `std value` and 3 x `std value` to get the threshold. I took CNPJs with more than 20 receipts -- which is a good sample and also shows frequency on hiring the companies' services -- for 1 or more congresspersons -- for we are analyzing companies in different states, and preliminary analysis (via Excel) shows a company is hired most of the time for a single congressperson.
# 
# The first scenario (2 x `std value`) shows we have 99 outliers. The second one (3 x `std value`) gives us 22 outliers.

# In[11]:

full_report_car.net_values.describe()


# 

# In[12]:

from scipy.stats import normaltest

def normaltest_pvalue(values):
    if len(values) >= 20:
        return normaltest(values).pvalue
    else:
        return 1

net_values_by_cnpj_1 = full_report_car.groupby('cnpj')['net_values']     .agg([len, np.mean, np.std, normaltest_pvalue])     .sort_values('len', ascending=False)     .reset_index()
net_values_by_cnpj_1['threshold'] = net_values_by_cnpj_1['mean'] +     2 * net_values_by_cnpj_1['std']
applicants_per_cnpj = full_report_car.groupby('cnpj')['applicant_id']     .aggregate(lambda x: len(set(x))).reset_index()     .rename(columns={'applicant_id': 'congresspeople'})
net_values_by_cnpj_1 = pd.merge(net_values_by_cnpj_1, applicants_per_cnpj)
net_values_by_cnpj_1.head()


# In[13]:

len(net_values_by_cnpj_1.query('normaltest_pvalue < .05')) / len(net_values_by_cnpj_1)


# In[14]:

def normaltest_pvalue(values):
    if len(values) >= 20:
        return normaltest(values).pvalue
    else:
        return 1

net_values_by_cnpj_2 = full_report_car.groupby('cnpj')['net_values']     .agg([len, np.mean, np.std, normaltest_pvalue])     .sort_values('len', ascending=False)     .reset_index()
net_values_by_cnpj_2['threshold'] = net_values_by_cnpj_2['mean'] +     3 * net_values_by_cnpj_2['std']
applicants_per_cnpj = full_report_car.groupby('cnpj')['applicant_id']     .aggregate(lambda x: len(set(x))).reset_index()     .rename(columns={'applicant_id': 'congresspeople'})
net_values_by_cnpj_2 = pd.merge(net_values_by_cnpj_2, applicants_per_cnpj)
net_values_by_cnpj_2.head()


# In[15]:

len(net_values_by_cnpj_2.query('normaltest_pvalue < .05')) / len(net_values_by_cnpj_2)


# In[16]:

data_with_threshold_1 = pd.merge(full_report_car, net_values_by_cnpj_1, on='cnpj')     .sort_values('net_values', ascending=False)


# In[17]:

data_with_threshold_2 = pd.merge(full_report_car, net_values_by_cnpj_2, on='cnpj')     .sort_values('net_values', ascending=False)


# In[18]:

outliers_1 = data_with_threshold_1.query('(congresspeople >= 1) & (len >= 20) & (net_values > threshold)')
print(len(outliers_1), outliers_1['net_values'].sum())


# In[19]:

outliers_2 = data_with_threshold_2.query('(congresspeople >= 1) & (len >= 20) & (net_values > threshold)')
print(len(outliers_2), outliers_2['net_values'].sum())


# #### Getting toll expenses

# In[20]:

companies_toll = companies[companies['main_activity_code'] == '52.21-4-00']


# In[21]:

data_toll = data[data['subquota_description'] == 'Taxi, toll and parking']


# In[22]:

dataset_toll = pd.merge(data_toll, companies_toll, how='outer',
                   left_on='cnpj_cpf', right_on='cnpj')


# In[23]:

congressperson_list_toll = data_toll[['congressperson_name', 
                            'congressperson_id', 
                            'net_values', 
                            'month', 
                            'year', 
                            'issue_date', 
                            'document_id',
                            'cnpj_cpf']]


# In[24]:

congressperson_expenses_dataset_toll = dataset_toll.groupby(['congressperson_name',
                                                    'applicant_id',
                                                    'year', 
                                                    'month', 
                                                    'issue_date',
                                                    'cnpj',
                                                    'name',
                                                    'city',
                                                    'state_y',
                                                    'document_id']).agg({'net_values':sum})
full_report_toll = congressperson_expenses_dataset_toll.reset_index()


# In[25]:

full_report_toll.name.count()


# In[26]:

full_report_toll.net_values.sum()


# In[27]:

full_report_toll.head()


# In[ ]:



