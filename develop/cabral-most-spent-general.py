
# coding: utf-8

# In[1]:

get_ipython().magic('matplotlib notebook')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[2]:

data = pd.read_csv('../data/2016-08-08-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# In[3]:

subquota_list = data['subquota_description'].unique()


# In[4]:

len(subquota_list)
print (subquota_list.item(4))


# ### Checking net values from all the receipts

# In[5]:

data.net_value.describe()


# In[6]:

grouped = data.groupby('cnpj_cpf', as_index=False)

print('{} total cnpj/cpfs, {} are unique'.format(len(data), len(grouped)))


# ### Creating a dataframe with the first supplier name for each cnpj_cpf:
# 

# In[7]:

cnpj_cpfs = []
names = []
for group in grouped:
    cnpj_cpfs.append(group[0])
    names.append(group[1].iloc[0].supplier)

names = pd.DataFrame({'cnpj_cpf': cnpj_cpfs, 'supplier_name': names})
names.head()



# ## CNPJs/CPFs that received most payments 

# In[8]:

spent = grouped.agg({'net_value': np.nansum}).sort_values(by='net_value', ascending=False)

spent = pd.merge(spent, names, on='cnpj_cpf')
spent.head(10)


# #### CNPJ/CPFs that received most payments divided per subquota

# In[29]:

subquota = dict()
sub_spent = dict()
sub_visit = dict()
for x in range(0, 18):
    foo = data[data.subquota_description == subquota_list.item(x) ]
    grouped = foo.groupby('cnpj_cpf', as_index=False)
    print(subquota_list.item(x) + ' have ' + '{} total cnpj/cpfs, {} are unique'.format(len(foo), len(grouped)))

    cnpj_cpfs = []
    names = []
    for group in grouped:
        cnpj_cpfs.append(group[0])
        names.append(group[1].iloc[0].supplier)

    names = pd.DataFrame({'cnpj_cpf': cnpj_cpfs, 'supplier_name': names})
    subquota[x] = names.head(10)
    #listing the ones with most spent amount of money
    spent = grouped.agg({'net_value': np.nansum}).sort_values(by='net_value', ascending=False)
    spent = pd.merge(spent, names, on='cnpj_cpf')
    sub_spent[x] = spent.head(10)
    #show the list with enterprises who received most number of visits
    visits = grouped['cnpj_cpf'].agg({'visits': len}).sort_values(by='visits', ascending=False)
    visits = pd.merge(visits, names, on='cnpj_cpf')
    sub_visit[x] = visits.head(10)


    


# # Dictionary for subquota

# In[23]:

for x in range(0,18):
    # print (x + ' = ' + subquota_list.item(x))
    print ( '{} for : '.format(x) + subquota_list.item(x))
print ('search using "subquota[your selected number]"')


# ### Use the cell below to search and understand each subquota

# In[44]:

#function to return all the info
def subquota_info(x):
    #return sub_visit[x], sub_spent[x]
    from IPython.display import display
    display(sub_visit[x])
    display(sub_spent[x])


# In[49]:

subquota_info(13)


# In[ ]:



