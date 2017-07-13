
# coding: utf-8

# # Conexão Reporter - Exploratory Analysis
# 
# 

# In[1]:

import numpy as np
import pandas as pd
from serenata_toolbox.datasets import Datasets


# In[3]:

datasets = Datasets('../data/')
datasets.downloader.download('2017-07-04-reimbursements.xz')


# In[18]:

datasets.downloader.download('2017-07-04-suspicions.xz')


# In[4]:

reimbursements = pd.read_csv('../data/2017-07-04-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str,
                             'document_id': np.int},
                      low_memory=False)


# In[5]:

reimbursements.columns


# ## Find current term biggest consumers
# 
# The idea is to find the top 3 lower house representatives with the highest amount of reimbursements considering all the years in office but that was elected in the last election. The current term started in 2015.

# we can find a table of lower house representatives in office using [this link](http://www2.camara.leg.br/deputados/pesquisa/arquivos/arquivo-formato-excel-com-informacoes-dos-deputados-1) bt there we only have 512 instead of the 513. So is a safer route to list the congresspeople using the reimbursements.

# In[6]:

current_term_reimbursements = reimbursements[reimbursements['year'] >= 2015].reset_index(drop=True)
current_term_reimbursements.shape


# In[8]:

len(list(set(current_term_reimbursements['congressperson_name'])))


# Remember that this number doesn't match 513 because we have names also for some leadership and seconds.

# In[71]:

current_term_congresspeople = list(set(current_term_reimbursements['congressperson_name']))

sorted(current_term_congresspeople)


# Those people elected for this term may have been elected before. I want to take into account exepenses that were made in previous mandates.

# In[10]:

reimbursements.shape


# In[11]:

filtered_reimbursements = reimbursements[reimbursements['congressperson_name'].isin(current_term_congresspeople)]


# In[12]:

filtered_reimbursements.shape


# In[61]:

keys = ['congressperson_name', 'congressperson_id', 'applicant_id']
grouped_by_representative = filtered_reimbursements.groupby(keys)['total_net_value'].agg([np.sum,len])                                     .reset_index()                                     .rename(columns={'total_net_value': 'sum', 
                                                     'len': 'expenses'})


# In[62]:

grouped_by_representative_top_5 = grouped_by_representative.sort_values('sum', ascending=False).head().reset_index(drop=True)
grouped_by_representative_top_5


# Each tof the top 3 conressperson chamber of deputies page:

# In[39]:

pd.set_option('display.max_colwidth', -1) # setting pandas so it won't truncate the html

congressperson_url = '<a href="http://www.camara.leg.br/internet/deputado/dep_Detalhe.asp?id={0}">link</a>'
grouped_by_representative_top_5['url'] = grouped_by_representative_top_5                                    .apply(lambda row: congressperson_url.format(row['congressperson_id']), axis=1)
grouped_by_representative_top_5


# In[40]:

from IPython.display import HTML
HTML(grouped_by_representative_top_5.to_html(escape=False))


# Interesting enough none of the top 5 is Bonifacio Andrada our lower house representative with the highest number of suspicions. So let's load the suspicions file and investigate a little further.

# In[19]:

suspicions = pd.read_csv('../data/2017-07-04-suspicions.xz')
suspicions.head()


# In[20]:

suspicions.shape


# Now let's filter suspicions from the role suspicions dataset that correspond to our current term.

# In[21]:

current_term_aplicant_ids = list(set(current_term_reimbursements['applicant_id']))
suspicions_current_term = suspicions[suspicions['applicant_id'].isin(current_term_aplicant_ids)]
suspicions_current_term.shape


# In[22]:

# this takes a lot of time! grab a cup of coffee
def is_suspect(row):
    return row.any()

suspicions_current_term['suspicious'] = suspicions_current_term.apply(lambda row: is_suspect(row[3:]), axis=1)


# In[23]:

only_suspicions_current_term = suspicions_current_term[suspicions_current_term['suspicious']]


# In[24]:

suspicions_current_term.shape


# In[25]:

only_suspicions_current_term.shape


# In[ ]:

# companies = pd.read_csv('../data/2017-05-21-companies-no-geolocation.xz', low_memory=False)


# In[29]:

current_term_applicant_ids = list(set(only_suspicions_current_term['applicant_id']))


# In[31]:

len(current_term_aplicant_ids)


# In[32]:

keys = ['applicant_id']
grouped_by_applicant = only_suspicions_current_term.groupby(keys)['suspicious'].agg(len)                                     .reset_index()


# In[55]:

grouped_by_applicant = grouped_by_applicant.sort_values('suspicious', ascending=False).head().reset_index(drop=True)
grouped_by_applicant


# In[66]:

top_5 = list(grouped_by_applicant.head()['applicant_id']) 
top_5 = list(map(str,top_5))
top_5


# In[77]:

top_5_with_suspicions = grouped_by_representative[grouped_by_representative['applicant_id'].isin(top_5)].head(10)
top_5_with_suspicions


# In[73]:

reimbursements[reimbursements['applicant_id']=='2439'].head(1)


# On TOP_5 doesn't show 'LIDERANÇA DO PT' because we'd filtered by congressperson_id. Make sense now since the leadership have special powers with the reimbursments. We MUST save this informations for future analysis like phantom enterprises and other analysis. 
