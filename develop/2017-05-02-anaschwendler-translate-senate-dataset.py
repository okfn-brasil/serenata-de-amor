
# coding: utf-8

# # Translating the Senate dataset
# As we say in [this article](https://medium.com/data-science-brigade/expandindo-a-serenata-de-amor-para-outras-esferas-48bed204d36d), we are expanding our project to other datasets, the first one will be the Senate Quota dataset.

# In[1]:

import pandas as pd

data = pd.read_csv('../data/senate_2017.csv',sep=';',encoding = "ISO-8859-1", skiprows=1)
data.columns = map(str.lower, data.columns)
data.shape


# In[2]:

data.head()


# In[3]:

data.iloc[0]


# ## Translating the dataset

# In[4]:

data.rename(columns={
        'ano': 'year',
        'mes': 'month',
        'senador': 'congressperson_name',
        'tipo_despesa': 'expense_type',
        'cnpj_cpf': 'cnpj_cpf',
        'fornecedor': 'supplier',
        'documento': 'document_id',
        'data': 'date',
        'detalhamento': 'expense_details',
        'valor_reembolsado': 'reimbursement_value',
    }, inplace=True)


# ## Expense types translation

# In[5]:

data['expense_type'] = data['expense_type'].astype('category')
data['expense_type'].cat.categories


# In[6]:

data['expense_type'].cat.rename_categories([
        'Rent of real estate for political office, comprising expenses concerning them',
        'Acquisition of consumables for use in the political office, including acquisition or leasing of software, postal expenses, acquisition of publications, rental of furniture and equipment',
        'Recruitment of consultancies, advisory services, research, technical work and other services in support of the exercise of the parliamentary mandate',
        'Publicity of parliamentary activity',
        'Locomotion, lodging, food, fuels and lubricants',
        'National air, water and land transport',
        'Private Security Services',
    ], inplace=True)


# In[7]:

data.head()


# In[8]:

data.iloc[0]


# ## Dataset properties
# The Federal Senate datasets are divided by years, we have data from the year `2008 - 2013`. It had experienced a few changes through time. So I'll be telling this dataset properties below:
# 
# * Until 2013 there wasn't a expense details field, but the other older dataset already have this field, but empty.
# * Until 2010 there wasn't the `National air, water and land transport` and `Private Security Services` categories of expense type, so when we start translating all the data we need to check if the dataset has those categories.
# * Studying the datasets to what we are doing by now, we can start using the `cnpj_cpf` classifier from the begining, since the data is pretty good to use.
# 
# This is a `work in progress` we are aiming to be adding it soon to our project.
