
# coding: utf-8

# # Piaui Herald - Exploratory Data Analysis
# Finding interesting cases for Rosie's column

# In[1]:

import numpy as np
import pandas as pd
from re import compile, search
from datetime import timedelta


# In[2]:

dataset = pd.read_csv('../../../serenata-data/2017-03-15-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str,
                             'document_id': np.int},
                      low_memory=False)


# ## Luxury Hotel

# We are aiming to find suspicious expenses in hotels, maybe someone spent the holidays in some luxury hotel and asked for reimbursement

# In[3]:

lodging = dataset[dataset['subquota_description'] == 'Lodging, except for congressperson from Distrito Federal']
keys = ['applicant_id','congressperson_id','cnpj_cpf', 'supplier']
grouped = lodging.groupby(keys)


# Number of Lodging expenses

# In[4]:

len(grouped)


# In[5]:

subquota_numbers = grouped['subquota_number'].agg(lambda x: ','.join(x)).reset_index()
subquota_numbers.head()


# In[6]:

document_ids = grouped['document_id'].agg(lambda x: tuple(x)).reset_index()
document_ids.head()


# In[7]:

net_values_sum = grouped['total_net_value'].agg({'sum': np.sum}).reset_index()
net_values_sum.head()


# In[8]:

aggregation = pd.merge(pd.merge(subquota_numbers, document_ids, on=keys),
                       net_values_sum, on=keys)
aggregation.head()


# Get net value by row

# In[9]:

def get_top_net_value(row):
    l = list(row['document_id'])
    values = []
    for reimbursement_id in l:
        values.append(float(dataset[dataset['document_id'] == reimbursement_id]['total_net_value']))
    return {'top_net_value':max(values), 'top_document':l[values.index(max(values))]}

top_things = aggregation.apply(func=get_top_net_value, axis='columns')
aggregation['top_net_value'], aggregation['top_document'] = "",""

for _ in range(len(top_things)):
    # paliative since DataFrame.replace() did not work ¯\_(ツ)_/¯
    aggregation.loc[_, 'top_net_value'] = top_things[_]['top_net_value']
    aggregation.loc[_, 'top_document'] = top_things[_]['top_document']

aggregation = aggregation.sort_values(by='top_net_value', ascending=False)
aggregation.head(10)


# ## Top eaters
# 
# Who were the congresspeople that ate more in one day and when?

# In[10]:

meals = dataset[dataset['subquota_description'] == 'Congressperson meal']
meals = meals.reset_index()


# In[11]:

keys = ['applicant_id','congressperson_name', 'issue_date']
meals_aggregation = meals.groupby(keys)['total_net_value'].                         agg({'sum': np.sum, 'expenses': len, 'mean': np.mean})
meals_aggregation['expenses'] = meals_aggregation['expenses'].astype(np.int)


# In[12]:

meals_agg_top20 = meals_aggregation.sort_values(['expenses', 'sum'], ascending=[False, False]).head(20)
meals_agg_top20 = pd.DataFrame(meals_agg_top20.reset_index())
meals_agg_top20.loc[:,'issue_date'] = pd.to_datetime(meals_agg_top20['issue_date'], errors='coerce')


# Bellow you can see the top 20 congresspeople that requested more reimbursements in one day

# In[13]:

meals_agg_top20.head(20)


# In[14]:

def create_jarbas_consult_congressperson_meal(row):
    d = timedelta(days=1)
    jarbas_api = "https://jarbas.serenatadeamor.org/#/applicantId"
    link = [jarbas_api, row['applicant_id'],
         'issueDateEnd', (row['issue_date'] + d).strftime('%Y-%m-%d'),
         'issueDateStart', row['issue_date'].strftime('%Y-%m-%d'),
         'subquotaId', '13']
    return '/'.join(link)

meals_agg_top20 = meals_agg_top20.assign(link_jarbas_consult=meals_agg_top20.                                          apply(func=create_jarbas_consult_congressperson_meal, axis=1))

print('Here are the links for those top 20')

for _ in range(20):
    print(meals_agg_top20.iloc[_]['link_jarbas_consult'])


# ### Priciest Meals
# What was the highest meal reimbursement, where it was made and by who?
# 
# Here are the top 20 priciest meals ever reimbursed.

# In[15]:

priciest_meals = meals[['document_id', 'issue_date',
                        'total_net_value', 'congressperson_name',
                        'supplier']]. \
                            sort_values('total_net_value', ascending=False).head(20)
priciest_meals.head(20)


# In[16]:

def create_jarbas_consult_document_id(row):
    jarbas_api = "https://jarbas.serenatadeamor.org/#/documentId"
    link = [jarbas_api, str(row['document_id'])]
    return '/'.join(link)


# In[17]:

priciest_meals = priciest_meals.assign(link_jarbas_consult=priciest_meals.                                          apply(func=create_jarbas_consult_document_id, axis=1))

print('Here are the links for those top 20')

for _ in range(20):
    print(priciest_meals.iloc[_]['link_jarbas_consult'])


# ## Roasted goat
# Some congress people seem to be very fond of roasted goat

# In[18]:

len(meals)


# In[19]:

bode = compile('BODE')
bode_bool = []
for _ in range(len(meals)):
    if bode.search(meals.loc[_, 'supplier']):
        bode_bool.append(True)
    else:
        bode_bool.append(False)


# In[20]:

bode_meals = meals[bode_bool]
keys = ['congressperson_id','cnpj_cpf', 'supplier', 'issue_date', 'document_id']
bode_meals_grouped = bode_meals.groupby(keys)

bode_meals_grouped = bode_meals_grouped['total_net_value'].agg({'expense': np.sum}).reset_index()
bode_meals_grouped = bode_meals_grouped.sort_values('expense', ascending=False)
bode_meals_top20 = bode_meals_grouped.head(20)
bode_meals_top20.head(20)


# In[21]:

bode_meals_top20 = bode_meals_top20.assign(link_jarbas_consult=bode_meals_top20.                                          apply(func=create_jarbas_consult_document_id, axis=1))

print('Here are the links for those top 20')

for _ in range(20):
    print(bode_meals_top20.iloc[_]['link_jarbas_consult'])


# ## Gas usage

# In[22]:

fuel = dataset[dataset['subquota_description'] == 'Fuels and lubricants']
fuel = fuel.reset_index()
fuel.loc[:,'issue_date'] = pd.to_datetime(fuel['issue_date'], errors='coerce')


# In[23]:

fuel['issue_date_day'] = fuel['issue_date'].apply(lambda date: date.day)
fuel['issue_date_month'] = fuel['issue_date'].apply(lambda date: date.month)
fuel['issue_date_year'] = fuel['issue_date'].apply(lambda date: date.year)


# In[24]:

fuel.head()


# In[25]:

keys = ['applicant_id', 'congressperson_id',
        'congressperson_name','issue_date_month',
        'issue_date_year']
fuel_grouped = fuel.groupby(keys)
fuel_aggregation = fuel_grouped['total_net_value'].agg({'sum': np.sum, 'expenses': len})
fuel_aggregation['expenses'] = fuel_aggregation['expenses'].astype(np.int)
fuel_aggregation = fuel_aggregation.sort_values(['sum','expenses'], ascending=[False, False])


# In[26]:

fa = pd.DataFrame(fuel_aggregation.reset_index())
fa = fa.assign(link_jarbas_consult="")
fa = fa.assign(issue_date_year=fa['issue_date_year'].apply(func=np.int))
fa = fa.assign(issue_date_month=fa['issue_date_month'].apply(func=np.int))


# In[27]:

fa.head(20)


# According to CEAP's Ato de Mesa document, it is only allowed to spend 6k of reais with fuels and lubricants:
# >IX - combustíveis e lubrificantes, até o limite inacumulável de R$ 6.000,00 (seis mil reais) mensais; (Inciso com 
# redação dada pelo Ato da Mesa no 49, de 3/9/2015)

# In[28]:

def create_jarbas_consult_fuel_and_lubricants(row):
    jarbas_api = "https://jarbas.serenatadeamor.org/#/applicantId"
    link = [jarbas_api, row['applicant_id'],
         'month', str(int(row['issue_date_month'])),
         'subquotaId', '3',
         'year', str(int(row['issue_date_year']))]
    return '/'.join(link)


# ### above the 6k gas quota
# Here I'll point the same 20 cases displayed above. Those are the top 20 highiest values spent on fuel
# 
# Here are the Jarbas search that lead to the top 20 above mentioned

# In[29]:

fa_above6k = fa.copy()
fa_above6k = fa_above6k.assign(link_jarbas_consult=fa_above6k.                                apply(func=create_jarbas_consult_fuel_and_lubricants, axis=1))
for _ in range(20):
    print(fa_above6k.iloc[_]['link_jarbas_consult'])


# ### Exactly 6k spent on fuel
# 
# Here are the top 20 most recent reimbursements that ask for exactly 6,000 reais.

# In[30]:

fa_exc6k = fa.sort_values('issue_date_year', ascending=False).query('sum == 6000').head(20).reset_index()
fa_exc6k.head(20)


# Here are the links for these top 20

# In[31]:

fa_exc6k = fa.copy()
fa_exc6k = fa_exc6k.assign(link_jarbas_consult=fa_exc6k.                            apply(func=create_jarbas_consult_fuel_and_lubricants, axis=1))
for _ in range(20):
    print(fa_exc6k.iloc[_]['link_jarbas_consult'])

