
# coding: utf-8

# # Election expenses
# 
# Recently we found a congressperson who made an allegedly postal service expense in a company created for his own benefit, for his next candidacy in elections.
# 
# We believe there are more cases like this one.

# In[1]:

import pandas as pd
import numpy as np

reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz',
                             dtype={'cnpj_cpf': np.str},
                             low_memory=False)
companies = pd.read_csv('../data/2016-09-03-companies.xz', low_memory=False)


# In[2]:

companies['cnpj'] = companies['cnpj'].str.replace(r'\D', '')


# In[3]:

dataset = pd.merge(reimbursements, companies,
                   left_on='cnpj_cpf', right_on='cnpj')


# In[4]:

is_election_company =     dataset['legal_entity'] == '409-0 - CANDIDATO A CARGO POLITICO ELETIVO'
suspect = dataset[is_election_company]
suspect.shape


# In[5]:

suspect['total_net_value'].sum()


# In[6]:

suspect['total_net_value'].describe()


# In[7]:

suspect['name'].sample(10)


# In[8]:

dataset['name'] = dataset['name'].astype(np.str)
contains_election_str = dataset['name'].str.lower().str.contains(r'(eleic)[(ao)(oes)]')
company_name_suspects = dataset[contains_election_str].index


# In[9]:

np.array_equal(suspect.index, company_name_suspects)


# In[10]:

import unicodedata

def normalize_string(string):
    if isinstance(string, str):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')


# In[11]:

suspect['congressperson_name'] =     suspect['congressperson_name'].apply(normalize_string)

suspect['name'] = suspect['name'].apply(normalize_string)
suspect[suspect.apply(lambda row: row['congressperson_name'] in row['name'], axis=1)]


# In[12]:

suspect[['congressperson_name', 'name']]


# ## Conclusion
# 
# Yes, there are more cases. Currently, 47 suspects. Not all of them were in congressperson's own benefit, but for other candidates. Still, could be reported to the Chamber of Deputies.

# In[ ]:



