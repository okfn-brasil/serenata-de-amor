
# coding: utf-8

# In[1]:

get_ipython().magic('matplotlib notebook')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[2]:

data = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                      dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str},
                      low_memory=False)


# In[3]:

data = data[data['year']==2016]


# # Data preparation

# In[4]:

meals = data[data.subquota_description == 'Congressperson meal']
meals.head()


# In[5]:

meals.total_net_value.describe()


# In[ ]:

plt.figure()
sns.distplot(meals.total_net_value, rug=True);


# In[ ]:

grouped = meals.groupby('cnpj_cpf', as_index=False)

print('{} total cnpj/cpfs, {} are unique'.format(len(meals), len(grouped)))


# ## Creating a dataframe with the first supplier name for each cnpj_cpf:

# In[ ]:

cnpj_cpfs = []
names = []
for group in grouped:
    cnpj_cpfs.append(group[0])
    names.append(group[1].iloc[0].supplier)

names = pd.DataFrame({'cnpj_cpf': cnpj_cpfs, 'supplier_name': names})
names.head()


# # CNPJs/CPFs that received most payments
# 
# The first issue with the dataset is that some places have more than one CNPJ, like SENAC.

# In[ ]:

spent = grouped.agg({'total_net_value': np.nansum}).sort_values(by='total_net_value', ascending=False)

spent = pd.merge(spent, names, on='cnpj_cpf')
spent.head(10)


# In[ ]:

plt.figure()
sns.distplot(spent['total_net_value'], rug=True);


# # CNPJs/CPFs that received most visits

# In[ ]:

visits = grouped['cnpj_cpf'].agg({'visits': len}).sort_values(by='visits', ascending=False)
visits = pd.merge(visits, names, on='cnpj_cpf')
visits.head(10)


# In[ ]:

plt.figure()
sns.distplot(visits['visits'], rug=True);


# # Combining the two previous dataframes to have an average spent value per visit:
# 
# We can identify places that were less frequented but charged high values. That shows some strange values such as R$ 4200 spent on just one visit in a place that looks like a car selling store (according to its name).

# In[ ]:

spent_visit = pd.merge(spent, visits, on=['cnpj_cpf', 'supplier_name'])

spent_visit.loc[:,'average_net_value'] = spent_visit.total_net_value/spent_visit.visits

spent_visit.sort_values(by='average_net_value', ascending=False, inplace=True)
spent_visit.head(20)


# This first part reveal some places that are almost never visited and have high values spent on. There are also places with some visits and high average value. For the less frequented places, there's not enough data to take an average value, but an overall average price for the entire dataset may be useful to highlight these cases.

# In[ ]:

meals.total_net_value.describe()


# From above, we see that the average value is **R\$ 65** and median value with a huge standard deviation of **R\$ 113**. The median value is **R\$ 46**.
# 
# An issue that bias the mean of the dataset is the existence of meals paid for groups.

# # Fitting a linear regression to the relation total_net_value x visits. It is expected that more visits means greater accumulated total_net_value:

# Here's a rather naïve assumption: the more a place is visited, the more money is spent in there. This is obviously not true since there are great differences in prices depending on which place is visited, but it turns out that a linear model wasn't too bad, but I think other models should be tested and compared later. From this part, the points that are too far **below** the line in the picture could be better investigated because they are too expensive (they get more money with less visits).

# In[ ]:

plt.figure()
sns.regplot(x="total_net_value", y="visits", data=spent_visit);


# # Analysis by CNPJ

# Now the analysis uses only expenses of single places (notice that there the two SENAC instances should be merged for a proper anaylis, but it wasn't done in this case). For that, I've used the [Outlier Labeling Rule](http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm), that uses the median instead of the mean, a measure that is more robust to outliers. The authors of this method recommend that any modified z-score greater than 3.5 should be considered as a potential outlier if the data is expected to come from a normal distribution. What follows is the application of this method for the first 10 most visited places, as it's not very helpful to make this to places less frequented.

# In[ ]:

from statsmodels.robust.scale import mad

# modified z-score
def modified_z_score(x):
    return (0.6745 * (x - np.median(x))) / mad(x)


# In[ ]:

#Analyzing the top10 most visited
for row in visits[:10].itertuples():
    print(row.cnpj_cpf, row.supplier_name)
    
    supplier_meals = meals[meals.cnpj_cpf == row.cnpj_cpf]
    print('{} meals'.format(len(supplier_meals)))
    
    mean = np.mean(supplier_meals.total_net_value)
    print('mean value = R$ {:.2f}'.format(mean))
    
    std = np.std(supplier_meals.total_net_value)
    print('standard deviation = R$ {:.2f}'.format(std))
    
    median = np.median(supplier_meals.total_net_value)
    print('median value = R$ {:.2f}'.format(median))
    
    modified_zscores = modified_z_score(supplier_meals.total_net_value)
    outlier_indexes = [i for i, score in enumerate(modified_zscores) if score > 3.5]
    
    print('{} outliers'.format(len(outlier_indexes)))
    print(supplier_meals.iloc[outlier_indexes][['document_id', 'total_net_value']]) 

