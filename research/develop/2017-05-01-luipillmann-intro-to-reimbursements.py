
# coding: utf-8

# # Intro to reimbursements: overview with visualization
# 
# This notebook provides an overview of the `2017-03-15-reimbursements.xz` dataset, which contains broad data regarding CEAP usage in all terms since 2009. 
# 
# It aims to provide an example of basic analyses and visualization by exploring topics such as:
# 
# - Average monthly spending per congressperson along the years
# - Seasonality in reimbursements
# - Reimbursements by type of spending
# - Which party has the most spending congressmen?
# - Which state has the most spending congressmen?
# - Who were the most hired suppliers by amount paid?
# - Which were the most expensive individual reimbursements?
# 
# Questions are not explicitly answered. Charts and tables are provided for free interpretation, some of them with brief commentaries from the author.
# 
# **Obs**.: original analysis was made considering data from 2009 to 2017 (mainly until 2016). One might want to filter by terms (e.g. 2010-2014) to make more realistic comparisons (spenditures by state, party, congressperson, etc.). Code cell #4 provides an example of how it could be done.
# 
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


# ## Filters depending on the scope of analysis
# Here, filters by state, party, years, etc. can be applied.
# 
# Obs.: chart commentaries provided might not remain valid depending on filters chosen. 

# In[4]:

# Filters only most recent years (from 2015)
#r = r[(r.year == 2015) | (r.year == 2016) | (r.year == 2017)]

#r.head()


# ## Questions & answers

# ### Evolution of average monthly spending along the years
# Are congressmen spending more today in relation to past years?

# #### How many congressmen in each year?

# In[5]:

years = r.year.unique()

# Computes unique names in each year and saves into a pd.Series
d = dict()
for y in years:
    d[y] = r[r.year == y].congressperson_name.nunique()

s = pd.Series(d)
s


# In[6]:

s.plot(kind='bar')
plt.title('Qtdy of congressmen listed per year')


# ##### Commentary
# Greater number of congressmen in 2011 and 2015 is due to term transitions which occur during the year.
# 
# ---

# #### How much did they spend, in average, per month in each year?
# This analysis takes into consideration the following elements:
# 
# - Main data: 
#     - Monthly average spending per congressman during each year
# - Relevant aspects for trend comparison:
#     - CEAP limit for each year (i.e. the maximum allowed quota increased during the years)
#     - Inflation indexes (i.e. prices of goods raised during the years)

# ##### Evolution of inflation (IPCA)

# In[7]:

# Source: http://www.ibge.gov.br/home/estatistica/indicadores/precos/inpc_ipca/defaultseriesHist.shtm
ipca_years = [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016]  
ipca_indexes = [0.0431, 0.0590, 0.0650, 0.0583, 0.0591, 0.0641, 0.1067, 0.0629]

ipca = pd.DataFrame({
    'year': ipca_years,
    'ipca': ipca_indexes
})


# Filters only by years in dataset
ipca = ipca[ipca['year'].isin(r.year.unique())].set_index('year')
ipca.head()


# ##### Maximum quota allowed (CEAP limits)
# There is information available for maximum CEAP for 2009 and 2017. Therefore, a simple compound growth rate (CAGR) is calculated from 2009 to 2017. Values for years in between are assumed to be a linear composition of the growth rate.

# In[8]:

states = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']

# Source: http://www2.camara.leg.br/a-camara/estruturaadm/diretorias/dirgeral/estrutura-1/deapa/portal-da-posse/ceap-1
ceap_2009 = [40711.32, 37318.73, 39734.17, 39554.50, 35540.51, 38705.50, 27977.66, 34080.83, 32317.69, 38429.49, 32856.38, 36949.65, 35924.24, 38499.17, 38319.91, 37992.68, 37344.18, 35412.67, 32550.32, 38963.25, 39828.33, 41612.80, 37256.00, 36337.92, 36578.43, 33730.95, 35993.76]

# Source: http://www2.camara.leg.br/comunicacao/assessoria-de-imprensa/cota-parlamentar
ceap_2017 = [44632.46, 40944.10, 43570.12, 43374.78, 39010.85, 42451.77, 30788.66, 37423.91, 35507.06, 42151.69, 36092.71, 40542.84, 39428.03, 42227.45, 42032.56, 41676.80, 40971.77, 38871.86, 35759.97, 42731.99, 43672.49, 45612.53, 40875.90, 39877.78, 40139.26, 37043.53, 39503.61]

ceap_limit_states = pd.DataFrame({
    'ceap_2009': ceap_2009,
    'ceap_2017': ceap_2017
}, index=states)

ceap_limit_states.head()


# In[9]:

all_years = ipca_years

# Calculates CAGR according to data available (CEAP@2009 and CEAP@2017), using the CEAP average among states
cagr = ((ceap_limit_states.ceap_2017.mean() / ceap_limit_states.ceap_2009.mean())**(1./(2017-2009)) - 1)

# Computes estimated CEAP values for years in between 2009 and 2017 using CAGR
ceap_values = []
for i in range(2017-2009):
    if i == 0:
        ceap_values.append(ceap_limit_states.ceap_2009.mean())
    elif i == (r.year.nunique() - 1):
        ceap_values.append(ceap_limit_states.ceap_2017.mean())
    else:
        ceap_values.append(ceap_values[i-1] * (1 + cagr))
        
# Creates df with all years
ceap_limit_years = pd.DataFrame({
    'year': all_years,
    'max_avg_ceap': ceap_values
})

# Filters only by years in dataset
ceap_limit_years = ceap_limit_years[ceap_limit_years['year'].isin(r.year.unique())].set_index('year')
ceap_limit_years.head()


# In[10]:

# Groups by name summing up spendings
a = r.groupby(['year']).sum().drop('month', 1)
a['congressmen_qty'] = s
a['avg_monthly_value_per_congressmen'] = a['total_net_value'] / a['congressmen_qty'] / 12
a = a.drop(2017, 0)  # Neglets 2017

# Adds columns for CEAP limits and IPCA indexes
a['max_avg_ceap'] = ceap_limit_years['max_avg_ceap']
a['pct_of_quota_used'] = (a['avg_monthly_value_per_congressmen'] / a['max_avg_ceap']) * 100
a['ipca'] = ipca['ipca']
a['acc_ipca'] = (a['ipca'] + 1).cumprod() - 1
a


# In[11]:

# Procedure to handle secondary Y axis
fig0, ax0 = plt.subplots()
ax1 = ax0.twinx()

y0 = a[['avg_monthly_value_per_congressmen', 'max_avg_ceap']].plot(kind='line', ax=ax0)#, label='Itens vendidos')
y1 = (a['acc_ipca']*100).plot(kind='line', secondary_y=False, style='g--', ax=ax1)#, label='Preço unitário')
y0.legend(loc=2) # bar legend to the left
y1.legend(loc=1) # line legend to the right

y0.set_ylim((0,50000))
#y1.set_ylim((0,50000))
y0.set_ylabel('CEAP usage and limit (R$)')
y1.set_ylabel('Accumulated IPCA index (%)')

plt.title('Avg. monthly congressmen spending vs. maximum quota and inflation idx.')
plt.show()
plt.close()


# ##### Commentary
# Although average spending has increased along the years, it can be due to both aspects considered: raises in prices and expanded limit for reimbursements.
# 
# The next chart shows how spending has increased with respect to quota limits.

# In[12]:

a.pct_of_quota_used.plot()
plt.ylim((0,100))
plt.title('Fluctuation of monthly CEAP spending per congressperson (% of max. quota)')


# ##### Commentary
# The chart shows that average spending has increased more than quota limits were raised (from ca. 40% to 60% of quota usage). This might be due to the steep rise in inflation levels, as observed in the previous chart.
# 
# ---

# ### Average monthly spending per congressperson along the years
# This table shows the data above detailed per congressperson.

# In[13]:

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

# In[14]:

r.groupby('month')    .sum()    .total_net_value    .sort_index()    .plot(kind='bar', rot=0)
    
plt.title('Fluctuation of reimbursements issued by months (R$)')


# ### Reimbursements by type of spending
# For what are congressmen most using their quota?

# In[15]:

r.groupby('subquota_description')    .sum()    .total_net_value    .sort_values(ascending=True)    .plot(kind='barh')
    
plt.title('Total spent by type of service (R$)')


# ##### Commentary
# This chart makes it clear what is prioritized by congressmen: publicity of their activity. Voters might judge whether this choice is reasonable or not.
# 
# ---

# ### Which party has the most spending congressmen?

# ##### How many congressmen in each party?

# In[16]:

parties = r.party.unique()
parties


# In[17]:

# Computes unique names in each state and saves into a pd.Series
d = dict()
for p in parties:
    d[p] = r[r.party == p].congressperson_name.nunique()

s = pd.Series(d)
s


# #### How much did congressmen from each party spend in the year, in average? 

# In[18]:

t = r.groupby('party').sum()
t = t.drop(['year', 'month'], 1)  # Removes useless columns

t['congressmen_per_party'] = s
years = r.year.nunique()


# In[19]:

t['monthly_value_per_congressperson'] = t['total_net_value'] / t['congressmen_per_party'] / (12*years)
t.sort_values(by='monthly_value_per_congressperson', ascending=False).head()


# In[20]:

t.monthly_value_per_congressperson    .sort_values(ascending=False)    .plot(kind='bar')

plt.title('Average monthly reimbursements per congressperson by party (R$)')


# ##### Commentary
# It is important to note that many congressmen change parties frequently. Therefore, anyone interested in drawing conclusions regarding parties might want to analyse the data in further detail than it is presented here.
# 
# ---

# ### Which state has the most spending congressmen?

# ##### How many congressmen in each state?

# In[21]:

states = r.state.unique()
states


# In[22]:

# Computes unique names in each party and saves into a pd.Series
d = dict()
for s in states:
    d[s] = r[r.state == s].congressperson_name.nunique()

s = pd.Series(d)
s


# #### How much did congressmen from each party spend in the year, in average? 

# ##### (!) Important: CEAP maximum value differs among states
# As already commented previously, CEAP max. quota varies among state, according to: http://www2.camara.leg.br/comunicacao/assessoria-de-imprensa/cota-parlamentar, 

# In[23]:

# CEAP maximum values from 2017
ceap_states = ceap_limit_states.drop('ceap_2009',1)
ceap_states.columns = ['monthly_max_ceap']  # Renames column to be compatible to code below
ceap_states.head()


# In[24]:

t = r.groupby('state').sum()
t = t.drop(['year', 'month'], 1)  # Removes useless columns

t['congressmen_per_state'] = s
t['monthly_max_ceap'] = ceap_states
years = r.year.nunique()


# In[25]:

t['monthly_value_per_congressperson'] = t['total_net_value'] / t['congressmen_per_state'] / (12*years)
t['ceap_usage'] = (t['monthly_value_per_congressperson'] / t['monthly_max_ceap']) * 100

t.sort_values(by='ceap_usage', ascending=False).head()


# In[26]:

t.ceap_usage    .sort_values(ascending=False)    .plot(kind='bar', rot=0)

plt.title('Average monthly CEAP usage per congressperson by state (% of max. quota)')


# #### Comparison between given state and the country's average

# In[27]:

t.head()


# In[28]:

country_average = t.ceap_usage.mean()
country_average


# In[29]:

# Parametrizes single state analysis
state = 'SP'
state_average = t.loc[state].ceap_usage
state_average


# In[30]:

s = pd.Series()
s['average_all_states'] = country_average
s[state] = state_average
s


# In[31]:

s.plot(kind='bar', rot=0)
plt.title('Average monthly CEAP usage per congressperson: ' + state + ' vs. rest of the country (% of max. quota)')


# ### Who were the top spenders of all time in absolute terms?

# In[32]:

r.groupby('congressperson_name')    .sum()    .total_net_value    .sort_values(ascending=False)    .head(10)


# In[33]:

r.groupby('congressperson_name')    .sum()    .total_net_value    .sort_values(ascending=False)    .head(30)    .plot(kind='bar')

plt.title('Total reimbursements issued per congressperson (all years)')


# ##### Commentary
# Because the dataset comprises 2009-2017, it might not be reasonable to draw any hard conclusions by looking to this chart alone. Some congressmen might have been elected for longer periods and that would reflect on higher reimbursement total values.
# 
# For a more detailed - hence coherent - analysis, one might want to make this comparison for each term (e.g. 2010-2014). That would better identify "top spenders" by comparing congressmen spendings on the same time period.
# 
# Another interesting analysis can be made by expanding the chart to all congressmen, not only the top 30. This enables a richer look at how discrepant top spenders are from the rest. To do that, just change `.head(30)\` argument in the previous cell.
# 
# ---

# ### Who were the most hired suppliers by amount paid?
# This analysis identifies suppliers by their unique CNPJ. It is worth noting that, commonly, some telecom carriers use different CNPJ for its subsidiaries in different states (e.g. TIM SP, TIM Sul, etc).

# In[34]:

sp = r.groupby(['cnpj_cpf', 'supplier', 'subquota_description'])        .sum()        .drop(['year', 'month'], 1)        .sort_values(by='total_net_value', ascending=False)

sp.reset_index(inplace=True)  
sp = sp.set_index('cnpj_cpf')

sp.head()


# In[35]:

cnpj = r.groupby('cnpj_cpf')        .sum()        .drop(['year', 'month'], 1)        .sort_values(by='total_net_value', ascending=False)

cnpj.head()


# In[36]:

# Adds supplier name besides total_net_value in cnpj df

cnpj['supplier'] = ''  # Creates empty column
cnpj = cnpj.head(1000)  # Gets only first 1000 for this analysis


# In[37]:

# Looks up for supplier names in sp df and fills cnpj df (it might take a while to compute...)

for i in range(len(cnpj)):
    try:
        cnpj.set_value(cnpj.index[i], 'supplier', sp.loc[cnpj.index[i]].supplier.iloc[0])
    except:
        cnpj.set_value(cnpj.index[i], 'supplier', sp.loc[cnpj.index[i]].supplier)

cnpj.head(10)


# In[38]:

# Fixes better indexing to plot in a copy
sp2 = cnpj.set_index('supplier')

sp2.head(30)    .plot(kind='bar')

plt.title('Most hired suppliers (unique CNPJ) by total amount paid (R$)')


# ##### Commentary
# In general, telecom carries were the suppliers with higher concentration of reimbursements. It is worth noting, however, that Telecommunication subquota accounts for only 8% of the reimbursents. This might suggest a 'long tail' pattern for other subquota types such as publicity, which accounts for 28% of all reimbursements.
# 
# Another aspect worth noting is the fact that some individual suppliers ("pessoas físicas") appear as top 15 suppliers (e.g. Mr. Douglas da Silva and Mrs. Joceli do Nascimento). One might wonder if such concentration of reimbursements for single-person suppliers is reasonable.

# In[39]:

pct_telecom = r[r['subquota_description'] == 'Telecommunication'].total_net_value.sum() / r.total_net_value.sum()
pct_telecom


# In[40]:

pct_publicity = r[r['subquota_description'] == 'Publicity of parliamentary activity'].total_net_value.sum() / r.total_net_value.sum()
pct_publicity


# #### Congressmen that hired the top supplier and how much they paid

# In[41]:

r.groupby(['cnpj_cpf', 'congressperson_name'])    .sum()    .sort_values(by='total_net_value', ascending=False)    .loc['02558157000162']    .total_net_value    .head(20)


# ### Which are the most expensive individual reimbursements?

# In[42]:

r = r.sort_values(by='total_net_value', ascending=False)
r.head(20)


# In[ ]:



