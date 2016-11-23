
# coding: utf-8

# In[1]:

get_ipython().magic('matplotlib inline')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from os import listdir
from os.path import join

plt.xkcd()


# In[2]:

def find_sum_of_values(df, aggregator, value):
    '''
    Return a dataframe with the statistics of values from "value" property
    aggregated by unique values from the column "aggregator"

    :params df: pandas dataframe to be sliced
    :params aggregator: dataframe column that will be
                        filtered by unique values
    :params value: dataframe column containing values to be summed
    :return: dataframe containing (for each aggregator unit):
        * property sum
        * property mean value
        * property max value
        * property mean value
        * number of occurences in total
    '''

    total_label = '{}_total'.format(value)
    max_label = '{}_max'.format(value)
    mean_label = '{}_mean'.format(value)
    min_label = '{}_min'.format(value)

    result = {
        'occurences': [],
        aggregator: df[aggregator].unique(),
        max_label: [],
        mean_label: [],
        min_label: [],
        total_label: [],
    }

    for item in result[aggregator]:
        if isinstance(df[aggregator].iloc[0], str):
            item = str(item)
        data = df[df[aggregator] == item]
        property_total = float(data[value].sum())
        occurences = float(data[value].count())

        result[total_label].append(property_total)
        result['occurences'].append(occurences)
        if occurences > 0:
            result[mean_label].append(property_total/occurences)
        else:
            result[mean_label].append(0)
        result[max_label].append(np.max(data[value]))
        result[min_label].append(np.min(data[value]))

    return pd.DataFrame(result).sort_values(by=aggregator)


def find_sum_of_values_per_period(df, aggregator, period_aggregator, value):
    '''
    Return a dataframe with a matrix containing unique values of
    dataframe column "aggregator" and dataframe column "period_aggregator".
    The values added are the sum of the "value" column.

    :params df: pandas dataframe to be sliced
    :params aggregator: dataframe column that will be
                        filtered by unique values
    :params period_ggregator: dataframe column that will be
                              filtered by unique values and compared with
                              aggregator column
    :params value: dataframe column containing values to be summed
    :return: dataframe containing aggregator vs period_aggregator with
             the sum of "value".
    '''

    periods = df[period_aggregator].unique() #1,2,3,4...

    result = {
        aggregator: df[aggregator].unique(), #fulano, ciclano...
    }

    for period in periods:
        result[period] = []

    for item in result[aggregator]:
        data = df[df[aggregator]==item]
        for period in periods:
            data_per_period = data[data[period_aggregator]==period]
            result[period].append(data_per_period[value].sum())
    return pd.DataFrame(result).sort_values(by=aggregator)


# In[3]:

data = pd.read_csv('../data/2016-11-22-reimbursements.xz',
                      dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str},
                      low_memory=False)


# In[4]:

meals = data[data['subquota_description']=='Congressperson meal']
meals.head()


# In[5]:

infos = {}

infos['total_spent'] = meals['total_net_value'].sum()
infos['initial_year'] = int(np.min(meals['year']))
infos['last_year'] = int(np.max(meals['year']))
infos


# # Total value spent of meals during all data records
# 
# Following data and graphs considers all expenditues since the initial record until the last data record.
# 

# In[6]:

plt.figure(figsize=(15,5))
plt.plot(meals['total_net_value']/1000)
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

# In[7]:

sum_per_person = find_sum_of_values(meals, 'congressperson_name', 'total_net_value')

if (sum_per_person['total_net_value_total'].sum() - infos['total_spent']) == 0:
    print('Values are ok!')


# In[8]:

infos['mean_value_spent'] = np.mean(sum_per_person['total_net_value_total'])
infos['max_value_spent'] = np.max(sum_per_person['total_net_value_total'])
infos['min_value_spent'] = np.min(sum_per_person['total_net_value_total'])
infos['min_value_spent_by'] = sum_per_person['congressperson_name'][sum_per_person['total_net_value_total'] == infos['min_value_spent']]
infos['max_value_spent_by'] = sum_per_person['congressperson_name'][sum_per_person['total_net_value_total'] == infos['max_value_spent']]

print('Mean value spent on meals: {}'.format(infos['mean_value_spent']))
print('Max value spent on meals: {}'.format(infos['max_value_spent']))
print('Max value spent on meals by: {}'.format(infos['max_value_spent_by']))
print('---')
print('Min value spent on meals: {}'.format(infos['min_value_spent']))
print('Min value spent on meals by: {}'.format(infos['min_value_spent_by']))


# # Top ten most expensive congress person

# In[9]:

sum_per_person.sort_values(by='total_net_value_total', ascending=False)[0:10]


# In[10]:

first_ten = sum_per_person.sort_values(by='total_net_value_total', ascending=False)[0:10]

major_ticks = first_ten['congressperson_name']


fig, ax1 = plt.subplots()
fig.set_figheight = 5

ax1.bar(range(10), first_ten['total_net_value_max']/1000, 0.25)
ax1.set_ylabel('Most expensive meal \n in thousands of Reais (R$)', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')
   
ax2 = ax1.twinx()
ax2.set_ylabel('Total value spent on meals \n in thousands of Reais (R$)', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')
ax2.plot(range(10), first_ten['total_net_value_total']/1000,'r')

ax1.set_xticks(range(10))
ax1.set_xticklabels(first_ten['congressperson_name'], rotation='vertical')
ax1.grid()


# #  List of expenditures on meals by month considereing all data records

# In[11]:

sum_by_month = find_sum_of_values(meals, 'month', 'total_net_value')

sum_by_month


# In[12]:

plt.bar(sum_by_month['month'], sum_by_month['total_net_value_total']/1000)
plt.title('Value spent on meals by month')
plt.ylabel('Thousands of Reais (R$)')
plt.xlabel('Month')
plt.grid()


# # Top ten most expensive parties

# In[13]:

sum_per_party = find_sum_of_values(meals, 'party', 'total_net_value')

sum_per_party.sort_values(by='total_net_value_total', ascending=False)[0:10]


# In[14]:

first_ten = sum_per_party.sort_values(by='total_net_value_total', ascending=False)[0:10]

major_ticks = first_ten['party']

fig, ax1 = plt.subplots()

ax1.bar(range(10), first_ten['total_net_value_max']/1000, 0.25)
ax1.set_ylabel('Most expensive meal /n in thousands of Reais (R$)', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')
   
ax2 = ax1.twinx()
ax2.set_ylabel('Total value spent on meals /n in thousands of Reais (R$)', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')
ax2.plot(range(10), first_ten['total_net_value_total']/1000,'r')

ax1.set_xticks(range(10))
ax1.set_xticklabels(first_ten['party'], rotation='vertical')
ax1.grid()


# # Data per year

# In[15]:

data_per_year = {}
for year in meals['year'].unique():
    data = meals[meals['year']==year]
    data_per_year[year] = {
        'data': data,
        'sum_per_parties': find_sum_of_values(data, 'party', 'total_net_value'),
        'sum_per_congressperson': find_sum_of_values(data, 'congressperson_name', 'total_net_value'),
        'congressperson_per_month': find_sum_of_values_per_period(data, 'congressperson_name', 'month', 'total_net_value'),
        'parties_per_month': find_sum_of_values_per_period(data, 'party', 'month', 'total_net_value'),
    }



# In[16]:

def find_most_expensive_monthly_expenditures(yearly_data, num=10):              
    sum_per_person = yearly_data['sum_per_congressperson']                      
    person_per_month = yearly_data['congressperson_per_month']                  
    most_expensive = sum_per_person.sort_values(by='total_net_value_total',           
                                                ascending=False)[0:num]         
    most_expensive_by_month = []                                                
    for name in most_expensive['congressperson_name']:                          
        most_expensive_by_month.append(                                         
            person_per_month[person_per_month['congressperson_name']==name]     
        )                                                                       
    return pd.concat(most_expensive_by_month)


# In[17]:

MONTHS = ['JAN', 'FEV', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AGO', 'SET', 'OCT', 'NOV', 'DEZ']
months = range(0, 12)


# # TEN MOST EXPENSIVE CONGRESS PERSON 2015

# In[18]:

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

# In[19]:

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

# In[20]:

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

# In[21]:

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

# In[22]:

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



