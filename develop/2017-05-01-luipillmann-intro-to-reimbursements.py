
# coding: utf-8

# # Intro to reimbursements: overview with visualization
# 
# This notebook provides an overview of the `2017-03-15-reimbursements.xz` dataset, which contains broad data regarding CEAP usage in all terms since 2009. 
# 
# It aims to provide an example of basic analyses and visualization by exploring topics such as:
# 
# - Evolution of avarege monthly spending along the years
# - Avarege monthly spending per congressperson along the years
# - Seasonality in reimbursements
# - Reimbursements by type of spending
# - Which party has the most spending congressmen?
# - Who were the top spenders of all time in absolute terms?
# - Who were the most hired suppliers by amount paid?
# - Which are the most expensive individual reimbursements?
# ---

# In[1]:

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pylab import rcParams

get_ipython().magic('matplotlib inline')

# Charts styling
plt.style.use('ggplot')
rcParams['figure.figsize'] = 15, 8
matplotlib.rcParams.update({'font.size': 14})
#rcParams['font.family'] = 'Georgia'

# Type setting for specific columns
#DTYPE = dict(cnpj=np.str, cnpj_cpf=np.str, ano=np.int16, term=np.str)

# Experimenting with 'category' type to reduce df size
DTYPE =dict(cnpj_cpf=np.str,            year=np.int16,            month=np.int16,            installment='category',            term_id='category',            term='category',            document_type='category',            subquota_group_id='category',            subquota_group_description='category',            #subquota_description='category',\
            subquota_number='category',\
            state='category',\
            party='category')


# In[2]:

reimbursements = pd.read_csv('../data/2017-03-15-reimbursements.xz',                              dtype=DTYPE, low_memory=False, parse_dates=['issue_date'])


# In[3]:

# Creates a DataFrame copy with fewer columns
r = reimbursements[['year', 'month', 'total_net_value', 'party', 'state', 'term', 'issue_date',        'congressperson_name', 'subquota_description','supplier', 'cnpj_cpf']]
r.head()


# ## Questions & answers

# ### Evolution of avarege monthly spending along the years
# Are congressmen spending more today in relation to past years?

# #### How many congressmen in each year?

# In[4]:

years = r.year.unique()

# Computes unique names in each year and saves into a pd.Series
d = dict()
for y in years:
    d[y] = len(r[r.year == y].congressperson_name.unique())

s = pd.Series(d)
s


# In[5]:

s.plot(kind='bar')
plt.title('Qtdy of congressmen listed per year')


# #### How much did they spend, in average, per month in each year?

# In[6]:

# Groups by name summing up spendings
a = r.groupby(['year']).sum().drop('month', 1)
a['congressmen_qty'] = s
a['monthly_value_per_congressmen'] = a['total_net_value'] / a['congressmen_qty'] / 12
a = a.drop(2017, 0)  # Neglets 2017


# In[7]:

a.monthly_value_per_congressmen.plot(kind='bar')
plt.title('Fluctuation of average monthly CEAP spending along the years (R$)')


# ### Avarege monthly spending per congressperson along the years
# This table shows the data above detailed per congressperson.

# In[8]:

# Groups by name summing up spendings
a = r.groupby(['congressperson_name', 'year'])    .sum()    .drop('month', 1)

# Computes average spending per month and unstacks
a['monthly_total_net_value'] = a['total_net_value'] / 12
a = a.drop('total_net_value', 1).unstack()

# Creates subtotal column to the right
a['mean'] = a.mean(axis=1)

a.head()


# ### Seasonality in reimbursements
# Out of curiosity,in which period of the year more reimbursements were issued?

# In[9]:

r.groupby('month')    .sum()    .total_net_value    .sort_index()    .plot(kind='bar')
    
plt.title('Fluctuation of reimbursements issued by months (R$)')


# ### Reimbursements by type of spending
# For what are congressmen most using their quota?

# In[10]:

r.groupby('subquota_description')    .sum()    .total_net_value    .sort_values(ascending=True)    .plot(kind='barh')
    
plt.title('Total spent by type of service (R$)')


# ### Which party has the most spending congressmen?

# ##### How many congressmen in each party?

# In[11]:

parties = r.party.unique()
parties


# In[12]:

# Computes unique names in each party and saves into a pd.Series
d = dict()
for p in parties:
    d[p] = len(r[r.party == p].congressperson_name.unique())

s = pd.Series(d)
s


# #### How much did congressmen from each party spend in the year, in average? 

# In[13]:

t = r.groupby('party').sum()
t = t.drop(['year', 'month'], 1)  # Removes useless columns

t['congressmen_per_party'] = s
years = len(r.year.unique())


# In[14]:

t['monthly_value_per_congressperson'] = t['total_net_value'] / t['congressmen_per_party'] / (12*years)
t.sort_values(by='monthly_value_per_congressperson', ascending=False).head()


# In[15]:

t.monthly_value_per_congressperson    .sort_values(ascending=False)    .plot(kind='bar')

plt.title('Average monthly reimbursements per congressperson by party (R$)')


# ### Who were the top spenders of all time in absolute terms?

# In[16]:

r.groupby('congressperson_name')    .sum()    .total_net_value    .sort_values(ascending=False)    .head(10)


# In[17]:

r.groupby('congressperson_name')    .sum()    .total_net_value    .sort_values(ascending=False)    .head(30)    .plot(kind='bar')

plt.title('Total reimbursements issued per congressperson (all years)')


# ### Who were the most hired suppliers by amount paid?
# This table shows the top service providers by amount received in total (all years)

# In[18]:

r.groupby(['cnpj_cpf', 'supplier', 'subquota_description'])    .sum()    .sort_values(by='total_net_value', ascending=False)    .head(20)


# #### Which congressmen hired the top supplier?

# In[19]:

r.groupby(['supplier', 'cnpj_cpf', 'subquota_description', 'congressperson_name'])    .sum()    .sort_values(by='total_net_value', ascending=False)    .loc['DOUGLAS CUNHA DA SILVA ME']    .total_net_value


# ### Which are the most expensive individual reimbursements?

# In[20]:

r = r.sort_values(by='total_net_value', ascending=False)
r.head(20)


# In[ ]:



