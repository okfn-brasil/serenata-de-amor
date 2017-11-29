
# coding: utf-8

# # Descriptive analysis of local transportation
# 

# This is Exploratory Descriptive Analisys of expendure with local transportation. So we will create three notebook to explore the data of the follows subquotas: 'Taxi, toll and parking', 'Automotive vehicle renting or charter' and 'Fuels and lubricants'. We basically used the same analysis used by Irio in his descriptive analysis of all dataset in https://github.com/datasciencebr/serenata-de-amor/blob/master/develop/2016-08-13-irio-descriptive-analysis.ipynb
# 
# The anlisys of others subquota ara in:
# 
# 'Automotive vehicle renting or charter': work in progress
# 
# 'Fuels and lubricants': work in progress

# ### This first notebook is about subquota 'Taxi, toll and parking'

# Importing the dataset

# In[111]:

get_ipython().magic('matplotlib inline')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import math


# In[30]:

data = pd.read_csv('../data/2017-03-14-reimbursements.xz',
                   parse_dates=[16],
                   low_memory=False,
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str,})


# All reimbursement of subquota 'Taxi, toll and parking' will be set in **data_taxi** variable, this is the main data who we will will use in this notebook.

# In[31]:

data_taxi = data[data['subquota_description'] == 'Taxi, toll and parking']


# Since 2013 was 70.088 documents of reimbursement.

# In[32]:

print(data_taxi.shape)


# In[33]:

data_taxi.head()


# In[34]:

data_taxi.iloc[0]


# All the expedures sums more than **R$2.2 Million**

# In[36]:

data_taxi['net_values'].sum()


# In[37]:

data_taxi['net_values'].describe()


# In[38]:

sns.distplot(data_taxi['net_values'])


# The most expensive reimbursement was **R$2.500**

# In[39]:

most_expensive_reimbursement =     data_taxi[data_taxi['net_values'] == data_taxi['net_values'].max()].iloc[0]
most_expensive_reimbursement


# Here we considered outliers all 0,5% biggest reimbursement values. We found 350 outliers in a total of R$338,060.46.

# In[71]:

data_taxi = data_taxi.sort_values('net_values', ascending=False)
outliers = data_taxi.head(math.floor(len(data_taxi)*0.005))
sns.distplot(outliers['net_values'])


# In[73]:

len(outliers)


# In[74]:

outliers['net_values'].sum()


# In[75]:

outliers


# ## Who are these applicants?

# In total 509 congressperson ask by reimbursement and most of them (75%) received R$5,364.90. 
# 
# But some congresperson received more them R$50.000,00 in the same perriod.

# In[77]:

len(data_taxi['applicant_id'].unique())


# In[78]:

applicants_by_net_value =     pd.DataFrame(data_taxi.groupby(['applicant_id'], as_index=False).sum()[['applicant_id', 'net_values']])


# In[79]:

congressperson_list = data_taxi[
    ['applicant_id', 'congressperson_name', 'party', 'state']]
congressperson_list = congressperson_list.     drop_duplicates('applicant_id', keep='first')
ranking = pd.merge(applicants_by_net_value,
                   congressperson_list,
                   how='left',
                   on='applicant_id').sort_values('net_values', ascending=False)
ranking.head(10)


# In[80]:

ranking['net_values'].describe()


# In[81]:

graph = sns.barplot(x='congressperson_name',
                    y='net_values',
                    data=ranking)
graph.axes.get_xaxis().set_ticks([]); None


# # Suppliers

# There are 1.797 suppliers, two of them are more than R$480.000. They are SINPETAXI, syndicate of taxi from Brasilia and CENTRO DE GESTAO DE MEIOS DE PAGAMENTO S.A., owner of SEM PARAR, company of payment of toll.

# In[83]:

suppliers_list = pd.DataFrame(data_taxi.groupby(['cnpj_cpf'], as_index=False)['net_values'].sum())
suppliers_list = suppliers_list.sort_values('net_values', ascending=False)
suppliers_list


# In[84]:

suppliers_list['net_values'].describe()


# In[52]:

sns.distplot(suppliers_list['net_values'])


# Here we considered outliers all 1% biggest suppliers. We found 17 outliers in a total of R$1.439.806.92
# 
# R$1.008.936,47 from SINPETAXI and SEM PARAR
# 
# R$430.870,44 from other companies

# In[102]:

outliers_suppliers = suppliers_list.head(math.floor(len(suppliers_list)*0.01))
sns.distplot(outliers_suppliers['net_values'])


# In[103]:

outliers_suppliers['net_values'].describe()


# In[104]:

outliers_suppliers['net_values'].sum()


# In[106]:

outliers_suppliers['net_values'].head(2).sum()


# In[108]:

outliers_suppliers['net_values'].tail(len(outliers_suppliers)-2).sum()


# In[54]:

outliers_suppliers = suppliers_list[~suppliers_list.isin(data_wo_outliers_suppliers)['cnpj_cpf']]
print(len(outliers_suppliers), len(outliers_suppliers) / len(suppliers_list))


# # Conclusion and next steps

# We could note there a long tail in the reimbursements, there a group of congresspeople who expend much more then others. We could observe too, two big suppliers, a taxi syndicate from Brasilia and a company of payment of toll. The sugestion of next stepes are:
# - split data of taxi, parking and toll.
# - check the expenses in the time (by year, month and day)
# - cross the data of "Taxi, toll and parking" with 'Automotive vehicle renting or charter' and 'Fuels and lubricants'
