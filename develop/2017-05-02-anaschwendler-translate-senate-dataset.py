
# coding: utf-8

# # Translating the Senate dataset
# As we say in [this article](https://medium.com/data-science-brigade/expandindo-a-serenata-de-amor-para-outras-esferas-48bed204d36d), we are expanding our project to other datasets, the first one will be the Senate Quota dataset.

# In[1]:

import pandas as pd

data = pd.read_csv('../data/2017-05-02-senado_2017.csv',sep=';',encoding = "ISO-8859-1", skiprows=1)
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
        'detalhamento': 'expense_detais',
        'valor_reembolsado': 'reimbursement_value',
    }, inplace=True)


# # Expense types translation

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


# In[ ]:



