
# coding: utf-8

# In[1]:

get_ipython().magic(u'matplotlib inline')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from os import listdir
from os.path import join
from utils import (concatenate_data_dataframes, 
                   find_sum_of_values,
                   find_sum_of_values_per_period)

plt.xkcd()


# In[2]:

data = concatenate_data_dataframes('../data/')


# In[3]:

meals = data[data['subquota_description']=='Congressperson meal']
meals.head()


# In[4]:

infos = {}

infos['total_spent'] = meals['net_value'].sum()
infos['initial_year'] = int(np.min(meals['year']))
infos['last_year'] = int(np.max(meals['year']))
infos


# # Total value spent of meals during all data records
# 
# Following data and graphs considers all expenditues since the initial record until the last data record.
# 

# In[5]:

plt.figure(figsize=(15,5))
plt.plot(meals['net_value']/1000)
plt.title('Value spent in one meal from {} to {}. \n Total value: {}'. format(infos['initial_year'],
                                                                              infos['last_year'],
                                                                              infos['total_spent']))
plt.ylabel('Thousand of Reais (R$)')
plt.xlabel('Number of Records')
plt.grid()


# #  List of total expenditures on meals by congress person
# 

# Attention! Ids can be nan from party expenses!
# 
# You can't use ids to get unique values

# In[6]:

sum_per_person = find_sum_of_values(meals, 'congressperson_name', 'net_value')

if (sum_per_person['net_value_total'].sum() - infos['total_spent']) == 0:
    print('Values are ok!')


# In[7]:

infos['mean_value_spent'] = np.mean(sum_per_person['net_value_total'])
infos['max_value_spent'] = np.max(sum_per_person['net_value_total'])
infos['min_value_spent'] = np.min(sum_per_person['net_value_total'])
infos['min_value_spent_by'] = sum_per_person['congressperson_name'][sum_per_person['net_value_total'] == infos['min_value_spent']]
infos['max_value_spent_by'] = sum_per_person['congressperson_name'][sum_per_person['net_value_total'] == infos['max_value_spent']]

print('Mean value spent on meals: {}'.format(infos['mean_value_spent']))
print('Max value spent on meals: {}'.format(infos['max_value_spent']))
print('Max value spent on meals by: {}'.format(infos['max_value_spent_by']))
print('---')
print('Min value spent on meals: {}'.format(infos['min_value_spent']))
print('Min value spent on meals by: {}'.format(infos['min_value_spent_by']))


# # Top ten most expensive congress person

# In[8]:

sum_per_person.sort_values(by='net_value_total', ascending=False)[0:10]


# In[9]:

first_ten = sum_per_person.sort_values(by='net_value_total', ascending=False)[0:10]

major_ticks = first_ten['congressperson_name']


fig, ax1 = plt.subplots()
fig.set_figheight = 5

ax1.bar(range(10), first_ten['net_value_max']/1000, 0.25)
ax1.set_ylabel('Most expensive meal \n in thousands of Reais (R$)', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')
   
ax2 = ax1.twinx()
ax2.set_ylabel('Total value spent on meals \n in thousands of Reais (R$)', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')
ax2.plot(range(10), first_ten['net_value_total']/1000,'r')

ax1.set_xticks(range(10))
ax1.set_xticklabels(first_ten['congressperson_name'], rotation='vertical')
ax1.grid()


# #  List of expenditures on meals by month considereing all data records

# In[10]:

sum_by_month = find_sum_of_values(meals, 'month', 'net_value')

sum_by_month


# In[11]:

plt.bar(sum_by_month['month'], sum_by_month['net_value_total']/1000)
plt.title('Value spent on meals by month')
plt.ylabel('Thousands of Reais (R$)')
plt.xlabel('Month')
plt.grid()


# # Top ten most expensive parties

# In[12]:

sum_per_party = find_sum_of_values(meals, 'party', 'net_value')

sum_per_party.sort_values(by='net_value_total', ascending=False)[0:10]


# In[13]:

first_ten = sum_per_party.sort_values(by='net_value_total', ascending=False)[0:10]

major_ticks = first_ten['party']

fig, ax1 = plt.subplots()

ax1.bar(range(10), first_ten['net_value_max']/1000, 0.25)
ax1.set_ylabel('Most expensive meal /n in thousands of Reais (R$)', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')
   
ax2 = ax1.twinx()
ax2.set_ylabel('Total value spent on meals /n in thousands of Reais (R$)', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')
ax2.plot(range(10), first_ten['net_value_total']/1000,'r')

ax1.set_xticks(range(10))
ax1.set_xticklabels(first_ten['party'], rotation='vertical')
ax1.grid()


# # Data per year

# In[14]:

data_per_year = {}
for year in meals['year'].unique():
    data = meals[meals['year']==year]
    data_per_year[year] = {
        'data': data,
        'sum_per_parties': find_sum_of_values(data, 'party', 'net_value'),
        'sum_per_congressperson': find_sum_of_values(data, 'congressperson_name', 'net_value'),
        'congressperson_per_month': find_sum_of_values_per_period(data, 'congressperson_name', 'month', 'net_value'),
        'parties_per_month': find_sum_of_values_per_period(data, 'party', 'month', 'net_value'),
    }



# In[ ]:

def find_most_expensive_monthly_expenditures(yearly_data, num=10):              
    sum_per_person = yearly_data['sum_per_congressperson']                      
    person_per_month = yearly_data['congressperson_per_month']                  
    most_expensive = sum_per_person.sort_values(by='net_value_total',           
                                                ascending=False)[0:num]         
    most_expensive_by_month = []                                                
    for name in most_expensive['congressperson_name']:                          
        most_expensive_by_month.append(                                         
            person_per_month[person_per_month['congressperson_name']==name]     
        )                                                                       
    return pd.concat(most_expensive_by_month)


# In[15]:

MONTHS = ['JAN', 'FEV', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AGO', 'SET', 'OCT', 'NOV', 'DEZ']
months = range(0, 12)


# # TEN MOST EXPENSIVE CONGRESS PERSON 2015

# In[16]:

YEAR = 2015
data = data_per_year[YEAR]
most_expensives = find_most_expensive_monthly_expenditures(data)
mm = most_expensives.set_index('congressperson_name').transpose()
index = [key for key in mm.keys()]

f = plt.figure(figsize=(15, 7))
plt.plot(months, mm[index[0]])
plt.plot(months, mm[index[1]])
plt.plot(months, mm[index[2]])
plt.plot(months, mm[index[3]])
plt.plot(months, mm[index[4]])
plt.plot(months, mm[index[5]], 'g')
plt.plot(months, mm[index[6]], 'k')
plt.plot(months, mm[index[7]], '0.45')
plt.plot(months, mm[index[8]], '--b')
plt.plot(months, mm[index[9]], '--k')
plt.xlim(0, 11)
plt.title('Expenditure of 10 most expensive congress person in {} by month'.format(YEAR))
plt.ylabel('Reais (R$)')
plt.legend(index, bbox_to_anchor=(1.4, 1))
ax1 = f.get_axes()[0]
ax1.set_xticks(range(12))
ax1.set_xticklabels(MONTHS, rotation=40)


# # TEN MOST EXPENSIVE CONGRESS PERSON 2014

# In[17]:

YEAR = 2014
data = data_per_year[YEAR]
most_expensives = find_most_expensive_monthly_expenditures(data)
mm = most_expensives.set_index('congressperson_name').transpose()
index = [key for key in mm.keys()]

f = plt.figure(figsize=(15, 7))
plt.plot(months, mm[index[0]])
plt.plot(months, mm[index[1]])
plt.plot(months, mm[index[2]])
plt.plot(months, mm[index[3]])
plt.plot(months, mm[index[4]])
plt.plot(months, mm[index[5]], 'g')
plt.plot(months, mm[index[6]], 'k')
plt.plot(months, mm[index[7]], '0.45')
plt.plot(months, mm[index[8]], '--b')
plt.plot(months, mm[index[9]], '--k')
plt.xlim(0, 11)
plt.title('Expenditure of 10 most expensive congress person in {} by month'.format(YEAR))
plt.ylabel('Reais (R$)')
plt.legend(index, bbox_to_anchor=(1.4, 1))
ax1 = f.get_axes()[0]
ax1.set_xticks(range(12))
ax1.set_xticklabels(MONTHS, rotation=40)


# # TEN MOST EXPENSIVE CONGRESS PERSON 2013

# In[18]:

YEAR = 2013
data = data_per_year[YEAR]
most_expensives = find_most_expensive_monthly_expenditures(data)
mm = most_expensives.set_index('congressperson_name').transpose()
index = [key for key in mm.keys()]

f = plt.figure(figsize=(15, 7))
plt.plot(months, mm[index[0]])
plt.plot(months, mm[index[1]])
plt.plot(months, mm[index[2]])
plt.plot(months, mm[index[3]])
plt.plot(months, mm[index[4]])
plt.plot(months, mm[index[5]], 'g')
plt.plot(months, mm[index[6]], 'k')
plt.plot(months, mm[index[7]], '0.45')
plt.plot(months, mm[index[8]], '--b')
plt.plot(months, mm[index[9]], '--k')
plt.xlim(0, 11)
plt.title('Expenditure of 10 most expensive congress person in {} by month'.format(YEAR))
plt.ylabel('Reais (R$)')
plt.legend(index, bbox_to_anchor=(1.4, 1))
ax1 = f.get_axes()[0]
ax1.set_xticks(range(12))
ax1.set_xticklabels(MONTHS, rotation=40)


# # TEN MOST EXPENSIVE CONGRESS PERSON 2012

# In[19]:

YEAR = 2012
data = data_per_year[YEAR]
most_expensives = find_most_expensive_monthly_expenditures(data)
mm = most_expensives.set_index('congressperson_name').transpose()
index = [key for key in mm.keys()]

f = plt.figure(figsize=(15, 7))
plt.plot(months, mm[index[0]])
plt.plot(months, mm[index[1]])
plt.plot(months, mm[index[2]])
plt.plot(months, mm[index[3]])
plt.plot(months, mm[index[4]])
plt.plot(months, mm[index[5]], 'g')
plt.plot(months, mm[index[6]], 'k')
plt.plot(months, mm[index[7]], '0.45')
plt.plot(months, mm[index[8]], '--b')
plt.plot(months, mm[index[9]], '--k')
plt.xlim(0, 11)
plt.title('Expenditure of 10 most expensive congress person in {} by month'.format(YEAR))
plt.ylabel('Reais (R$)')
plt.legend(index, bbox_to_anchor=(1.4, 1))
ax1 = f.get_axes()[0]
ax1.set_xticks(range(12))
ax1.set_xticklabels(MONTHS, rotation=40)


# # TEN MOST EXPENSIVE CONGRESS PERSON 2011

# In[20]:

YEAR = 2011
data = data_per_year[YEAR]
most_expensives = find_most_expensive_monthly_expenditures(data)
mm = most_expensives.set_index('congressperson_name').transpose()
index = [key for key in mm.keys()]

f = plt.figure(figsize=(15, 7))
plt.plot(months, mm[index[0]])
plt.plot(months, mm[index[1]])
plt.plot(months, mm[index[2]])
plt.plot(months, mm[index[3]])
plt.plot(months, mm[index[4]])
plt.plot(months, mm[index[5]], 'g')
plt.plot(months, mm[index[6]], 'k')
plt.plot(months, mm[index[7]], '0.45')
plt.plot(months, mm[index[8]], '--b')
plt.plot(months, mm[index[9]], '--k')
plt.xlim(0, 11)
plt.title('Expenditure of 10 most expensive congress person in {} by month'.format(YEAR))
plt.ylabel('Reais (R$)')
plt.legend(index, bbox_to_anchor=(1.4, 1))
ax1 = f.get_axes()[0]
ax1.set_xticks(range(12))
ax1.set_xticklabels(MONTHS, rotation=40)


# In[ ]:



