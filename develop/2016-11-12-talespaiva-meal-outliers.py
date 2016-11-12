
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

data.head()


# In[4]:

meals = data[data.subquota_description == 'Congressperson meal']


# In[5]:

meals.net_value.describe()


# In[6]:

plt.figure()
sns.distplot(meals.net_value, rug=True);


# In[7]:

grouped = meals.groupby('cnpj_cpf', as_index=False)

print('{} total cnpj/cpfs, {} are unique'.format(len(meals), len(grouped)))


# In[8]:

# create a df with the first supplier name for each cnpj_cpf
cnpj_cpfs = []
names = []
for group in grouped:
    cnpj_cpfs.append(group[0])
    names.append(group[1].iloc[0].supplier)

names = pd.DataFrame({'cnpj_cpf': cnpj_cpfs, 'supplier_name': names})
names.head()


# ### Let's try to figure out which places are the preferred ones.
# 
# #### CNPJs that received most payments:

# In[9]:

spent = grouped.agg({'net_value': np.nansum}).sort_values(by='net_value', ascending=False)

spent = pd.merge(spent, names, on='cnpj_cpf')
spent.head(10)


# In[10]:

plt.figure()
sns.distplot(spent['net_value'], rug=True);


# #### Most frequented:

# In[11]:

visits = grouped['cnpj_cpf'].agg({'visits': len}).sort_values(by='visits', ascending=False)
visits = pd.merge(visits, names, on='cnpj_cpf')
visits.head(10)


# In[12]:

plt.figure()
sns.distplot(visits['visits'], rug=True);


# ### Now by average net value. We can identify places that were less frequented but charged high values.

# In[13]:

spent_visit = pd.merge(spent, visits, on=['cnpj_cpf', 'supplier_name'])

spent_visit.loc[:,'average_net_value'] = spent_visit.net_value/spent_visit.visits

spent_visit.sort_values(by='average_net_value', ascending=False, inplace=True)
spent_visit.head(20)


# ### We see a meal expenditure at a car selling store? Maybe this should be better investigated.

# In[14]:

meals[meals.cnpj_cpf == '04780541000130']


# ### Fitting a linear regression to the relation net_value x visits. It is expected that more visits means greater accumulated net_value:

# In[15]:

plt.figure()
sns.regplot(x="net_value", y="visits", data=spent_visit);


# # Analysis by CNPJ

# In[16]:

# Outlier Labeling Rule: http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
from statsmodels.robust.scale import mad

# modified z-score
def modified_z_score(x):
    return (0.6745 * (x - np.median(x))) / mad(x)


# In[17]:

#Analyzing the top10 most visited
for row in visits[:10].itertuples():
    print(row.cnpj_cpf, row.supplier_name)
    
    supplier_meals = meals[meals.cnpj_cpf == row.cnpj_cpf]
    print('{} meals'.format(len(supplier_meals)))
    
    mean = np.mean(supplier_meals.net_value)
    print('mean value = R$ {:.2f}'.format(mean))
    
    std = np.std(supplier_meals.net_value)
    print('standard deviation = R$ {:.2f}'.format(std))
    
    median = np.median(supplier_meals.net_value)
    print('median value = R$ {:.2f}'.format(median))
    
    modified_zscores = modified_z_score(supplier_meals.net_value)
    outlier_indexes = [i for i, score in enumerate(modified_zscores) if score > 3.5]
    
    print('{} outliers'.format(len(outlier_indexes)))
    print(supplier_meals.iloc[outlier_indexes][['document_id', 'net_value']])
    
    print()

