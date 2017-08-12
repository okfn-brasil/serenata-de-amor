
# coding: utf-8

# # Checking federal senate reimbursements
# 
# This analysis is a study in progress that shows hows does Federal Senate datasets works. Like in the `chamber_of_deputies` reimbursements, we will need to concat all the datasets, and clean what is necessary to clean.
# What we need to see:
# - [x] Concat all the nine datasets
# - [x] Fix the `date` field to datetime
# - [x] Clean the `cnpj_cpf` field
# - [x] Check the dataset peculiarities
# - [x] Check if a `group_by` is necessary

# In[1]:

import pandas as pd
import numpy as np
from datetime import date

FIRST_YEAR = 2008
NEXT_YEAR = date.today().year + 1

filenames = ['../data/2017-05-09-federal-senate-{}.xz'.format(year) for year in range(FIRST_YEAR, NEXT_YEAR)]

dataset = pd.DataFrame()

for filename in filenames:
    data = pd.read_csv(filename, encoding = "utf-8")
    dataset = pd.concat([dataset, data])


# In[2]:

len(dataset)


# In[3]:

dataset.head()


# In[4]:

dataset['date'] = pd.to_datetime(dataset['date'], errors='coerce')
dataset['cnpj_cpf'] = dataset['cnpj_cpf'].str.replace(r'\D', '')


# In[5]:

dataset.query('date != "NaT"').head()


# In[6]:

dataset[dataset['expense_details'].notnull()].head()


# In[7]:

(dataset['document_id'].isnull()).sum()


# In[8]:

(dataset['document_id'].notnull()).sum()


# In[9]:

print(len(dataset['document_id'].unique()))


# ## Dataset peculiarities
# 
# The dataset has many peculiarities, some of them I already mentioned in [my last notebook](2017-05-02-anaschwendler-translate-senate-dataset.ipynb):
# * Until 2013 there wasn't a expense details field, but the other older dataset already have this field, but empty.
# * Until 2010 there wasn't the `National air, water and land transport` and `Private Security Services` categories of expense type, so when we start translating all the data we need to check if the dataset has those categories.
# * Studying the datasets to what we are doing by now, we can start using the `cnpj_cpf` classifier from the begining, since the data is pretty good to use.
# 
# But there is a few more things that need to be considered like:
# * There is a total of 203547 reimbursements até agora.
# * and 19543 of them are whithout `document_id` field
# * which means that 184004 of the have `document_id` field and NOT ALL OF THEM ARE UNIQUE, so we need to check if the reimbursements are made like `chamber_of_deputies` and we need to group them by `document_id`. 
# * The datasets have no `cnpj_cpf`, `supplier`, `document_id`, `date`, `expense_details` fields from 2008 until the beggining of 2009.
# * The datasets only have complete information after 2011.

# ## Decisions
# 
# After all those analysis we decided that we will only clean up the `date` and `cnpj_cpf` and after that we will make another study with all the things that we can discover exploring the fields.
# That is what will be done, if you want, you can check the progress in [this PR](https://github.com/datasciencebr/serenata-toolbox/pull/53)
# 
# Thanks @jtemporal and @cuducos for all feedbacks given <3
