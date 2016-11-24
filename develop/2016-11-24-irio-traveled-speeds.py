
# coding: utf-8

# # Traveled speeds
# 
# The Quota for Exercise of Parliamentary Activity says that meal expenses can be reimbursed just for the politician, excluding guests and assistants. Creating a feature with information of traveled speed from last meal can help us detect anomalies compared to other expenses.
# 
# Since we don't have in structured data the time of the expense, we want to anylize the group of expenses made in the same day.
# 
# * Learn how to calculate distance between two coordinates.
# * Filter "Congressperson meal" expenses.
# * Order by date.
# * Merge `reimbursements.xz` dataset with `companies.xz`, so we have latitude/longitude for each expense.
# * Remove expenses with less than 12 hours of distance between each other.
# 
# ...
# 
# 
# * Filter specific congressperson.

# In[1]:

import pandas as pd
import numpy as np

reimbursements = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                             dtype={'cnpj_cpf': np.str})


# In[2]:

reimbursements.iloc[0]


# In[3]:

reimbursements = reimbursements[reimbursements['subquota_description'] == 'Congressperson meal']
reimbursements.shape


# In[4]:

reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], errors='coerce')
reimbursements.sort_values('issue_date', inplace=True)


# In[5]:

companies = pd.read_csv('../data/2016-09-03-companies.xz', low_memory=False)
companies.shape


# In[6]:

companies.iloc[0]


# In[7]:

companies['cnpj'] = companies['cnpj'].str.replace(r'[\.\/\-]', '')


# In[8]:

dataset = pd.merge(reimbursements, companies, left_on='cnpj_cpf', right_on='cnpj')
dataset.shape


# In[9]:

dataset.iloc[0]


# Remove party leaderships from the dataset before calculating the ranking.

# In[15]:

dataset = dataset[dataset['congressperson_id'].notnull()]
dataset.shape


# And also remove companies mistakenly geolocated outside of Brazil.

# In[45]:

is_in_brazil = (dataset['longitude'] < -34.7916667) &     (dataset['latitude'] < 5.2722222) &     (dataset['latitude'] > -33.742222) &     (dataset['longitude'] > -73.992222)
dataset = dataset[is_in_brazil]
dataset.shape


# In[38]:

# keys = ['applicant_id', 'issue_date']
keys = ['congressperson_name', 'issue_date']
aggregation = dataset.groupby(keys)['total_net_value'].     agg({'sum': np.sum, 'expenses': len, 'mean': np.mean})


# In[39]:

aggregation['expenses'] = aggregation['expenses'].astype(np.int)


# In[43]:

aggregation.sort_values(['expenses', 'sum'], ascending=[False, False]).head(10)


# In[50]:

len(aggregation[aggregation['expenses'] > 7])


# In[74]:

keys = ['congressperson_name', 'issue_date']
cities = dataset.groupby(keys)['city'].     agg({'city': lambda x: len(set(x)), 'city_list': lambda x: ','.join(set(x))}).sort_values('city', ascending=False)


# In[70]:

cities.head()


# In[71]:

cities[cities['city'] >= 4].shape


# Would be helpful for our analysis to have a new column containing the traveled distance in this given day.

# In[49]:

from geopy.distance import vincenty as distance
from IPython.display import display

x = dataset.iloc[0]
display(x[['cnpj', 'city', 'state_y']])
y = dataset.iloc[20]
display(y[['cnpj', 'city', 'state_y']])
distance(x[['latitude', 'longitude']],
         y[['latitude', 'longitude']])


# In[89]:

dataset.shape


# In[90]:

dataset[['latitude', 'longitude']].dropna().shape


# In[ ]:

from itertools import tee

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def calculate_distances(x):
    coordinate_list = x[['latitude', 'longitude']].values
    distance_list = [distance(*coordinates_pair).km
                     for coordinates_pair in pairwise(coordinate_list)]
    return np.nansum(distance_list)

distances = dataset.groupby(keys).apply(calculate_distances)


# In[108]:

distances = distances.reset_index()     .rename(columns={0: 'distance_traveled'})     .sort_values('distance_traveled', ascending=False)
distances.head()


# In[ ]:



