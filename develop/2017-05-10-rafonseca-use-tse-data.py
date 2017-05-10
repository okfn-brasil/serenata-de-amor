
# coding: utf-8

# ### TSE data example
# This is just a small example of how to use tse data. 
# In this script we filter the candidates in order to obtain a dataframe containing only politicians that were elected at least once.

# In[1]:

import pandas as pd
import numpy as np
import os


# In[2]:

DATASET_PATH= os.path.join(os.pardir,'data','2017-05-10-tse-candidates.xz')


# In[3]:

# Loading csv
cand_df=pd.read_csv(DATASET_PATH,encoding='utf-8',dtype='category',)# setting dtype to category instead of str cuts by more than a half RAM usage
cand_df.columns


# In[4]:

### Here, we quickly check the data using  value_counts() to get the frequency on each column
for name, col in cand_df.iteritems():
    print ('\t',name,'\n')
    print (col.value_counts())


# ### Only elected politicians
# Now, we process candidacies data to obtain a list of elected politicians
# We use 'result' to figure out who has been elected. It is better to use the description column then the code column, since the codes dont seem to be consistent along the years.
# 

# In[5]:

ind_elected= (cand_df.result=='elected') | (cand_df.result=='elected_by_party_quota')
# ind_elected|=cand_df.result=='alternate'# should we consider it?
ind_elected= cand_df.index[ind_elected]


# In[6]:

politicians_df=cand_df.loc[ind_elected,['cpf','name','post','location','state','year']]


# In[7]:

politicians_df.sort_values('name')


# It is quite curious that alphabetically ordered in this way, the last politician is called...

# If we want to keep only the list of politicians we keep only cpf and name and remove the duplicates

# In[8]:

politicians_df[['cpf','name']].drop_duplicates().sort_values('name')

