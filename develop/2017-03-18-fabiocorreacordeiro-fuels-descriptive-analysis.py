
# coding: utf-8

# # Descriptive analysis of local transportation
# 

# This is Exploratory Descriptive Analisys of expendure with local transportation. So we will create three notebook to explore the data of the follows subquotas: 'Taxi, toll and parking', 'Automotive vehicle renting or charter' and 'Fuels and lubricants'. We basically used the same analysis used by Irio in his descriptive analysis of all dataset in https://github.com/datasciencebr/serenata-de-amor/blob/master/develop/2016-08-13-irio-descriptive-analysis.ipynb
# 
# The analysis of others subquota are in:
# 
# 'Automotive vehicle renting or charter': work in progress
# 
# 'Taxi, toll and parking': work in progress

# ### This first notebook is about subquota 'Fuels and lubricants'

# Importing the dataset

# In[71]:

get_ipython().magic('matplotlib inline')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import math


# In[72]:

data = pd.read_csv('../data/2017-03-14-reimbursements.xz',
                   parse_dates=[16],
                   low_memory=False,
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str,})


# All reimbursement of subquota 'Fuels and lubricants' will be set in **data_fuel** variable, this is the main data who we will will use in this notebook.

# In[73]:

data_fuel = data[data['subquota_description'] == 'Fuels and lubricants']


# Since 2013 was 569.729 documents of reimbursement.

# In[74]:

print(data_fuel.shape)


# In[75]:

data_fuel.head()


# In[76]:

data_fuel.iloc[0]


# All the expedures sums more than **R$127 Million**

# In[77]:

data_fuel['net_values'].sum()


# In[78]:

data_fuel['net_values'].describe()


# In[79]:

sns.distplot(data_fuel['net_values'],bins=100)


# The most expensive reimbursement was **R$6000**

# In[80]:

most_expensive_reimbursement =     data_fuel[data_fuel['net_values'] == data_fuel['net_values'].max()].iloc[0]
most_expensive_reimbursement


# Here we considered outliers all reimbursements that exceed the **max cost of R$948,90**.
# 
# The max cost was calculate using the worst case, biggest gas tank in brazilian market (Ford F-250 with 110l tank), the cost of gas in the most expense gas station in Brasil (R4,99) and 10l of most expensive lubricant (R$40). Most of service stations don't charge to change lubricants.
# 
# **We found 24,480 outliers in a total of R$66,952,239.53, representing 4,2% of total.**
# 
# There is a big concentration of reimbursements with value of R$4,500
# 
# Fonts:
# Tanks size: https://panelinhanet.wordpress.com/2013/02/20/combustivel-quantos-litros-cabem-no-tanque-do-seu-veiculo/ in 18/mar/2017
# Cost of gas: http://www.anp.gov.br/preco/prc/Resumo_Semanal_Combustiveis.asp in 18/mar/2017
# Lubricant capacity: http://www.autoideia.com.br/capacidade_oleo_motor_automoveis&codmar=ford
# Cost of lubricant: http://www.mercadomineiro.com.br/pesquisa/oleo-lubrificante-pesquisa-precos

# In[81]:

fuel_cost = 4.99
fuel_tank = 110
lubricant_cost = 40
lubricant_capacity = 10
max_cost = fuel_cost*fuel_tank + lubricant_cost*lubricant_capacity
max_cost


# In[82]:

outliers = data_fuel[data_fuel['net_values'] > max_cost].sort_values('net_values', ascending=False)
sns.distplot(outliers['net_values'],bins=100)


# In[83]:

print (len(outliers),len(outliers)/len(data_fuel))


# In[84]:

outliers['net_values'].sum()


# In[85]:

outliers


# Now let's investigate more about reimbursements with value of R$4,500. There are 1912 reimbursements with this value, for 195 congresspeople in 281 suppliers.

# In[86]:

outlier_4500 = data_fuel[data_fuel['net_values'] == 4500].sort_values('congressperson_id', ascending=False)
len(outlier_4500)


# In[87]:

len(outlier_4500['cnpj_cpf'].unique())


# In[88]:

len(outlier_4500['congressperson_id'].unique())


# In[89]:

outlier_4500


# ## Who are these applicants?

# In total 1124 congressperson ask by reimbursement and most of them (75%) received R$175,007 or less.
# 
# But some congressmen received more than R$400.000,00 in the same period.

# In[90]:

len(data_fuel['applicant_id'].unique())


# In[91]:

applicants_by_net_value =     pd.DataFrame(data_fuel.groupby(['applicant_id'], as_index=False).sum()[['applicant_id', 'net_values']])


# In[92]:

congressperson_list = data_fuel[
    ['applicant_id', 'congressperson_name', 'party', 'state']]
congressperson_list = congressperson_list.     drop_duplicates('applicant_id', keep='first')
ranking = pd.merge(applicants_by_net_value,
                   congressperson_list,
                   how='left',
                   on='applicant_id').sort_values('net_values', ascending=False)
ranking.head(10)


# In[93]:

ranking['net_values'].describe()


# In[94]:

graph = sns.barplot(x='congressperson_name',
                    y='net_values',
                    data=ranking)
graph.axes.get_xaxis().set_ticks([]); None


# Now let's investigate the congresspeople who asked for reimbursement greater than max cost.

# In[95]:

congressperson_outlier = outliers[
    ['applicant_id', 'congressperson_name', 'party', 'state']]
congressperson_outlier = congressperson_outlier.     drop_duplicates('applicant_id', keep='first')
ranking_outlier = pd.merge(applicants_by_net_value,
                   congressperson_outlier,
                   how='left',
                   on='applicant_id').sort_values('net_values', ascending=False)
ranking_outlier.head(10)


# # Suppliers

# In[96]:

suppliers_list = pd.DataFrame(data_fuel.groupby(['cnpj_cpf','supplier'], as_index=False)['net_values'].sum())
suppliers_list = suppliers_list.sort_values('net_values', ascending=False)
suppliers_list.head(10)


# In[97]:

suppliers_list['net_values'].describe()


# In[98]:

sns.distplot(suppliers_list['net_values'])


# Here we check all suppliers of outliers reimbursements (greater than max cost)

# In[99]:

suppliers_outliers = pd.DataFrame(outliers.groupby(['cnpj_cpf','supplier'], as_index=False)['net_values'].sum())
suppliers_outliers = suppliers_outliers.sort_values('net_values', ascending=False)
suppliers_outliers.head(10)


# In[100]:

suppliers_outliers['net_values'].describe()


# In[101]:

suppliers_outliers['net_values'].sum()


# # Conclusion and next steps

# We found many suspicious reimbursement that exceed the value of the biggest cost possible of a fuel tank and an oil change. We found 24,480 outliers, R$66,952,239.53, representing 4,2% of total. 
# 
# **This analysis must be cross-checked by other members of the Serenade of Love and, if it is robust enough, included in Rosie's algorithms.**
# 
# There are a unusual concentration of reimbursement of R$4,500. 
# 
# The next steps are:
# - Check the expenses in the time (by year, month and day)
# - Cross the data of 'Fuels and lubricants' with "Taxi, toll and parking" and 'Automotive vehicle renting or charter'. 
# - Cross data of congresspeople and suppliers.
