
# coding: utf-8

# # Descriptive analysis of local transportation
# 

# This is Exploratory Descriptive Analisys of expendure with local transportation. So we will create three notebook to explore the data of the follows subquotas: 'Taxi, toll and parking', 'Automotive vehicle renting or charter' and 'Fuels and lubricants'. We basically used the same analysis used by Irio in his descriptive analysis of all dataset in https://github.com/datasciencebr/serenata-de-amor/blob/master/develop/2016-08-13-irio-descriptive-analysis.ipynb
# 
# The analysis of others subquota are in:
# 
# 'Fuels and lubricants': work in progress
# 
# 'Taxi, toll and parking': https://github.com/datasciencebr/serenata-de-amor/blob/master/develop/2017-03-15-fabiocorreacordeiro-taxi-descriptive-analysis.ipynb

# ### This notebook is about subquota 'Automotive vehicle renting or charter' 

# Importing the dataset

# In[2]:

get_ipython().magic('matplotlib inline')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import math


# In[3]:

data = pd.read_csv('../data/2017-03-14-reimbursements.xz',
                   parse_dates=[16],
                   low_memory=False,
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str,})


# All reimbursement of subquota 'Automotive vehicle renting or charter' will be set in **data_rent** variable, this is the main data who we will will use in this notebook.

# In[4]:

data_rent = data[data['subquota_description'] == 'Automotive vehicle renting or charter']


# Since 2013 was 15.625 documents of reimbursement.

# In[5]:

print(data_rent.shape)


# In[6]:

data_rent.head()


# In[7]:

data_rent.iloc[0]


# All the expedures sums more than **R$64 Million**

# In[8]:

data_rent['net_values'].sum()


# In[9]:

data_rent['net_values'].describe()


# In[10]:

sns.distplot(data_rent['net_values'],bins=200)


# The most expensive reimbursement was **R$10,900**

# In[11]:

most_expensive_reimbursement =     data_rent[data_rent['net_values'] == data_rent['net_values'].max()].iloc[0]
most_expensive_reimbursement


# When we see the 'net_values' distribution we note a wired concentration near of value of R$10,000. So we considered outliers all reimbursement value greater than 9,500.
# 
# We found 1,014 reimbursement in a total of R$10,271,519.16

# In[12]:

outliers = data_rent[data_rent['net_values'] > 9500]
sns.distplot(outliers['net_values'],bins=150)


# In[13]:

print (len(outliers),len(outliers)/len(data_rent))


# In[14]:

outliers['net_values'].sum()


# In[15]:

outliers


# ## Who are these applicants?

# In total 649 congressperson ask by reimbursement and they received a mean of R$98,845.47 (the same price of a car model 2017 http://veiculos.fipe.org.br?carro/toyota/3-2017/002112-1/2017/g/chdwdshts7l18).

# In[16]:

len(data_rent['applicant_id'].unique())


# In[17]:

applicants_by_net_value =     pd.DataFrame(data_rent.groupby(['applicant_id'], as_index=False).sum()[['applicant_id', 'net_values']])


# In[18]:

congressperson_list = data_rent[
    ['applicant_id', 'congressperson_name', 'party', 'state']]
congressperson_list = congressperson_list.     drop_duplicates('applicant_id', keep='first')
ranking = pd.merge(applicants_by_net_value,
                   congressperson_list,
                   how='left',
                   on='applicant_id').sort_values('net_values', ascending=False)
ranking.head(10)


# In[19]:

ranking['net_values'].describe()


# In[20]:

graph = sns.barplot(x='congressperson_name',
                    y='net_values',
                    data=ranking)
graph.axes.get_xaxis().set_ticks([]); None


# Now let's investigate the congresspeople who asked for reimbursement greater than R$9,500.

# In[21]:

congressperson_outlier = outliers[
    ['applicant_id', 'congressperson_name', 'party', 'state']]
congressperson_outlier = congressperson_outlier.     drop_duplicates('applicant_id', keep='first')
ranking_outlier = pd.merge(applicants_by_net_value,
                   congressperson_outlier,
                   how='left',
                   on='applicant_id').sort_values('net_values', ascending=False)
ranking_outlier.head(10)


# When we analyze the expenses of 2016 of congressman Assis do Couto we noted he use all the value allowed in subquota. He maintained a rented car during all year, not only during work travel. All his expenses was R$124.998,05 and the same car new cost R159.256,00 (http://veiculos.fipe.org.br?carro/mitsubishi/3-2017/022132-5/32000/d/jb1s59gpwqcb).

# Jan- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/5914104.pdf
# 
# Feb- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/5933052.pdf
# 
# Mar- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/5977587.pdf
# 
# Apr- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6018073.pdf
# 
# Mai- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6018302.pdf
# 
# Jun- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6062144.pdf
# 
# Jul- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6077662.pdf
# 
# Ago- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6098398.pdf
# 
# Sep- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6125142.pdf
# 
# Oct- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6154773.pdf
# 
# Nov- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2016/6169069.pdf
# 
# Dez- http://www.camara.gov.br/cota-parlamentar//documentos/publ/1542/2017/6193296.pdf

# # Suppliers

# In[22]:

suppliers_list = pd.DataFrame(data_rent.groupby(['cnpj_cpf','supplier'], as_index=False)['net_values'].sum())
suppliers_list = suppliers_list.sort_values('net_values', ascending=False)
suppliers_list.head(10)


# In[23]:

suppliers_list['net_values'].describe()


# In[24]:

sns.distplot(suppliers_list['net_values'])


# Here we check all suppliers of outliers reimbursements (greater than R$9,500)

# In[25]:

suppliers_outliers = pd.DataFrame(outliers.groupby(['cnpj_cpf','supplier'], as_index=False)['net_values'].sum())
suppliers_outliers = suppliers_outliers.sort_values('net_values', ascending=False)
suppliers_outliers.head(10)


# In[26]:

suppliers_outliers['net_values'].describe()


# In[27]:

suppliers_outliers['net_values'].sum()


# # Conclusion and next steps

# We didn't found anything clearly illegal, but we noted that some congressmen use this subquota to maintain a car constantly rented to use, not only rent a car when are travel. This kind of use could be a divergence of the main idea of this subquota.
# 
# The next steps are:
# - Check the expenses in the time (by year, month and day)
# - Cross the data of 'Fuels and lubricants' with "Taxi, toll and parking" and 'Fuels and lubricants'. 
# - Cross data of congresspeople and suppliers.
