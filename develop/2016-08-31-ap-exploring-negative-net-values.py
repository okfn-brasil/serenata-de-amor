
# coding: utf-8

# # Exploring negative net_values

# This [issue](https://github.com/datasciencebr/serenata-de-amor/issues/29) explains the goal of this analysis.

# In[1]:

import numpy as np
import pandas as pd


# In[2]:

data = pd.read_csv('../data/2016-08-08-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# 374.484 expenses in total

# In[3]:

print(data.shape)


# In[4]:

data.head()


# In[5]:

data.iloc[0]


# There's an expense with a `net_value` of R$`-9240,77`.

# In[6]:

data['net_value'].describe()


# Taking a look at the expense with the highest negative value:

# In[7]:

highest_negative_expense =     data[data['net_value'] == data['net_value'].min()].iloc[0]
highest_negative_expense


# How many expenses with the same `document_number`?

# In[8]:

expenses = data[data['document_number'] == highest_negative_expense['document_number']]
len(expenses)


# In[9]:

expenses['net_value'].describe()


# In this specific case, it seems that Sibá Machado purchased a flight ticket of R\$ 9127,11 on 15/09/2015. He canceled it on the same day and the returned amount was R\$ 9240.77, generating an actual **profit** of R\$ 113,66 (1,3%). Not bad mr Sibá.

# In[10]:

expenses.iloc[0]


# In[11]:

expenses.iloc[1]


# There are **17.646** of them and all have "Flight ticket issue" as `subquota_description`.

# In[12]:

negative_documents = data[data['net_value'] < 0]
len(negative_documents)


# In[13]:

negative_documents['subquota_description'].unique()


# Summing negative expenses and postive expenses with the same `document_number` as one of the negatives gives us **31.104** expenses. We have a big discrepancy: **17.646** negatives and **13.458** positives.

# In[14]:

negatives_and_counterparts = data[data['document_number'].isin(negative_documents['document_number'])]

len(negatives_and_counterparts)


# In[15]:

counterparts = negatives_and_counterparts[negatives_and_counterparts['net_value'] > 0]

len(counterparts)


# In[16]:

# If every negative document is to have a pair, we're short on positive ones by:
len(negative_documents) - len(counterparts)


# What comes to mind is: 
# - Those remaining **4.188** are negative expenses without a corresponding positive one?;
# - The document numbers are messed up? Maybe something like: "Bilhete: 957-2117.270689" for the negative and "Vôo: 957-2117.270689" for the positive;
# - The net_values are messed up? Maybe some positive one were registered as negatives;
# - The positive expense is not in this dataset? Maybe in an older one;

# Taking from negatives without counterparts (**31.104**) and removing every document with a matching document number in counterparts(**13.458**) gives us a total of **4.458** expenses. More than the **4.188** I antecipaded.

# In[17]:

negatives_without_counterparts = negative_documents[~negative_documents.document_number.isin(counterparts['document_number'])]

len(negatives_without_counterparts)


# It seems we're dealing with expenses with the same document number were both are negatives...

# In[18]:

len(negatives_without_counterparts['document_number'].unique())


# Here I'm importing previous year's dataset

# In[19]:

old_data = pd.read_csv('../data/2016-08-08-previous-years.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# In[20]:

print(old_data.shape)


# It seems we have **6.655** matches for our negatives without counterparts (**4.458**) list's document numbers in the old data. It's more than the number of negatives.

# In[21]:

old_data_counterparts = old_data[old_data['document_number'].isin(negatives_without_counterparts['document_number'])]

len(old_data_counterparts)


# **Most** but not all are positives.

# In[22]:

old_data_only_positives = old_data_counterparts[old_data_counterparts['net_value'] > 0]

len(old_data_only_positives)

