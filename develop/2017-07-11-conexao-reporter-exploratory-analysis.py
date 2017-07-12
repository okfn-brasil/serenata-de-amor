
# coding: utf-8

# # Conexão Reporter - Exploratory Analysis
# 
# 

# In[1]:

import numpy as np
import pandas as pd


# In[2]:

reimbursements = pd.read_csv('../data/2017-07-04-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str,
                             'document_id': np.int},
                      low_memory=False)


# In[3]:

reimbursements.columns


# ## Find current term biggest consumers
# 
# The idea is to find the top 3 lower house representatives with the highest amount of reimbursements considering all the years in office but that was elected in the last election. The current term started in 2015.

# we can find a table of lower house representatives in office using [this link](http://www2.camara.leg.br/deputados/pesquisa/arquivos/arquivo-formato-excel-com-informacoes-dos-deputados-1) bt there we only have 512 instead of the 513. So is a safer route to list the congresspeople using the reimbursements.

# In[4]:

current_term_reimbursements = reimbursements[reimbursements['year'] >= 2015].reset_index(drop=True)
current_term_reimbursements.shape


# In[5]:

len(list(set(current_term_reimbursements['congressperson_name'])))


# Remember that this number doesn't match 513 because we have names also for some leadership and seconds.

# In[6]:

current_term_congresspeople = list(set(current_term_reimbursements['congressperson_name']))

sorted(current_term_congresspeople)


# Those people elected for this term may have been elected before. I want to take into account exepenses that were made in previous mandates.

# In[7]:

reimbursements.shape


# In[8]:

filtered_reimbursements = reimbursements[reimbursements['congressperson_name'].isin(current_term_congresspeople)]


# In[9]:

filtered_reimbursements.shape


# In[10]:

keys = ['congressperson_name', 'congressperson_id', 'applicant_id']
grouped_by_representative = filtered_reimbursements.groupby(keys)['total_net_value'].agg(np.sum)                                     .reset_index()                                     .rename(columns={'total_net_value': 'sum'})


# In[11]:

grouped_by_representative = grouped_by_representative.sort_values('sum', ascending=False).head().reset_index(drop=True)
grouped_by_representative


# Each tof the top 3 conressperson chamber of deputies page:

# In[12]:

pd.set_option('display.max_colwidth', -1) # setting pandas so it won't truncate the html

congressperson_url = '<a href="http://www.camara.leg.br/internet/deputado/dep_Detalhe.asp?id={0}">link</a>'
grouped_by_representative['url'] = grouped_by_representative                                     .apply(lambda row: congressperson_url.format(row['congressperson_id']), axis=1)
grouped_by_representative


# In[13]:

from IPython.display import HTML
HTML(grouped_by_representative.to_html(escape=False))


# Interesting enough none of the top 5 is Bonifacio Andrada our lower house representative with the highest number of suspicions. So let's load the suspicions file and investigate a little further.

# In[14]:

suspicions = pd.read_csv('../data/2017-07-04-suspicions.xz')
suspicions.head()


# In[15]:

suspicions.shape


# Now let's filter suspicions from the role suspicions dataset that correspond to our current term.

# In[32]:

current_term_aplicant_ids = list(set(current_term_reimbursements['applicant_id']))
suspicions_current_term = suspicions[suspicions['applicant_id'].isin(current_term_aplicant_ids)]
suspicions_current_term.shape


# In[ ]:




# In[33]:

# this takes a lot of time! grab a cup of coffee
def is_suspect(row):
    return row.any()

suspicions_current_term['suspicious'] = suspicions_current_term.apply(lambda row: is_suspect(row[3:]), axis=1)


# In[34]:

only_suspicions_current_term = suspicions_current_term[suspicions_current_term['suspicious']]


# In[35]:

suspicions_current_term.shape


# In[ ]:




# In[36]:

only_suspicions_current_term.shape


# In[ ]:

# companies = pd.read_csv('../data/2017-05-21-companies-no-geolocation.xz', low_memory=False)

