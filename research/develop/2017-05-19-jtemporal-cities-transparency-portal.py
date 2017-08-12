
# coding: utf-8

# # First Study on Brazilian Cities Transparency Portal
# In this dataset we have a population projection for each Brazilian city in the year of 2013.
# 
# 

# In[1]:

import pandas as pd
import numpy as np

# We first collected the data with population estimatives, 
# we can use it later to do some comparisions or to use it later
cities = pd.read_excel('../data/Cidades - estimativa 2013.xlsx',
                       converters={'COD. UF': np.str, 'COD. MUNIC': np.str},
                       sheetname=None, header=0)


# In[2]:

data = pd.DataFrame()
for key in cities.keys():
    data = pd.concat([data, cities[key]])
    
data = data.reset_index(drop=True)
data.shape


# We should see 5570 rows because that's the number of cities that IBGE says that Brazil have. The different amount of rows leads me to believe there are metadata from the `.xlsx` messing with our data

# ## Translating column names

# In[3]:

data.rename(columns={
        'UF': 'state',
        'COD. UF': 'state_id',
        'COD. MUNIC': 'city_id',
        'NOME DO MUNICÍPIO': 'city_name',
        'POPULAÇÃO ESTIMADA': 'population_projection'
    }, inplace=True)
data.head()


# ## Formating `city_id`
# 
# Formatting `city_id` to conform with the ids displayed on the Brazilian cesus files

# In[4]:

data['city_id'] = data['city_id'].apply(lambda x: x.zfill(5))


# ## Checking out a `unique_id` for each city

# In[5]:

data[data['city_id'] == '00108']


# In[6]:

UNIQUE_IDS = data.loc[:,['state_id', 'city_id']]

for i in range(len(UNIQUE_IDS['state_id'])):
    UNIQUE_IDS.loc[i,'ids'] = '{}{}'.format(UNIQUE_IDS.loc[i,'state_id'],
                                              UNIQUE_IDS.loc[i,'city_id'])

UNIQUE_IDS.head()


# In[7]:

len(set(UNIQUE_IDS['ids']))


# In[8]:

UNIQUE_IDS.shape


# In[9]:

brazilian_states = {'RO': 'rondonia',
                    'AC': 'acre',
                    'AM': 'amazonas',
                    'RR': 'roraima',
                    'PA': 'para',
                    'AP': 'amapa',
                    'TO': 'tocantis',
                    'MA': 'maranhao',
                    'PI': 'piaui',
                    'CE': 'ceara',
                    'RN': 'rio_grande_do_norte',
                    'PB': 'paraiba',
                    'PE': 'pernambuco',
                    'AL': 'alagoas',
                    'SE': 'sergipe',
                    'BA': 'bahia',
                    'MG': 'mina_gerais',
                    'ES': 'epirito_santo',
                    'RJ': 'rio_de_janeiro',
                    'SP': 'sao_paulo',
                    'PR': 'parana',
                    'SC': 'santa_catarina', 
                    'RS': 'rio_grande_do_sul',
                    'MS': 'mato_grosso_do_sul',
                    'MT': 'mato_grosso',
                    'GO': 'goias',
                    'DF': 'distrito_federal'}

census_link = "ftp.ibge.gov.br/Censos/Censo_Demografico_2010/resultados/total_populacao_{}.zip"


# ## Gathering cities with @cuducos Brazilian Cities script
# 
# @cuducos had already made a script with all Brazilian Cities and its code and state associated, here in [this repository](https://github.com/cuducos/brazilian-cities).
# 
# We checked and it is the best way to get the cities in the right way.

# In[10]:

from serenata_toolbox.datasets import fetch

fetch('2017-05-22-brazilian-cities.csv', '../data')


# In[11]:

brazilian_cities = pd.read_csv('../data/2017-05-22-brazilian-cities.csv')
brazilian_cities.head()


# In[12]:

brazilian_cities.shape


# ## Normalizing its form
# 
# It is necessary to normalize all information in order to use it to our necessities, so we managed to:
# - Lowercase all states
# - Remove all acentuation and normalize cities names
# - And for our case we remove spaces to generate the pattern we want

# In[13]:

brazilian_cities['state'] = brazilian_cities['state'].apply(str.lower)


# In[14]:

import unicodedata

def normalize_string(string):
    if isinstance(string, str):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')


# In[15]:

brazilian_cities['normalized_name'] = brazilian_cities['name'].apply(lambda x: normalize_string(x))
brazilian_cities['normalized_name'] = brazilian_cities['normalized_name'].apply(lambda x: x.replace(' ', ''))


# In[16]:

brazilian_cities.head()


# ## Getting all cities that are part of Transparency Portal
# 
# There are some cities that we already know that have a page with transparency and open data. The main objective here is to find how many cities have that.
# 
# Pattern: `{city}-{state}.portaltp.com.br`

# In[17]:

portal_url = 'https://{}-{}.portaltp.com.br/'
brazilian_cities['transparency_portal_url'] = brazilian_cities.apply(lambda row: portal_url.format(
                                                                                        row['normalized_name'],
                                                                                        row['state']), axis=1)
brazilian_cities.head(20)


# (Getting all of the status code for each city might take a while so we added the prints only for feedback)

# In[18]:

import requests
    
def get_status(url):
    try:
        print(requests.head(url).status_code)
        return requests.head(url).status_code
    except requests.ConnectionError:
        print(404)
        return 404


# In[19]:

get_ipython().run_cell_magic('time', '', "colatina = brazilian_cities[brazilian_cities['code'] == 320150]['transparency_portal_url'].values[0]\nstatusOK = get_status(colatina)\n\nabaete = brazilian_cities[brazilian_cities['code'] == 310020]['transparency_portal_url'].values[0]\nstatusNOK = get_status(abaete)")


# In[20]:

br_cities = brazilian_cities.loc[:10,:].copy()


# In[21]:

get_ipython().run_cell_magic('time', '', "br_cities.loc[:,'status_code'] = br_cities.apply(lambda x: get_status(x['transparency_portal_url']), axis=1)")


# In[22]:

br_cities


# This will take too long considering we have 5570 cities to address.
# 
# Let's try using [grequests](https://pypi.python.org/pypi/grequests).
# 
# I know that we can find two different status code in the first 10 cities urls test. So let's use those 10 to test grequests ;)

# In[23]:

import grequests

rs = (grequests.get(u) for u in list(br_cities['transparency_portal_url']))


# In[24]:

def exception_handler(request, exception):
    return 404

responses = grequests.map(rs, exception_handler=exception_handler)


# In[25]:

codes = [int(x) for x in br_cities['status_code'].values]

print(pd.unique(codes), pd.unique(responses))


# In[26]:

responses


# The result above got me wondering where were those 200 statuses code we've seen before. I tested the code on the command line and they are there. So a little reasearch and I found that apparently it is not possible to run async tasks easily on a jupyter notebook [ref](http://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Asynchronous.html).
# 
# With that in mind we decided to write a script that generates the infomartion we want: Open Data url for each brazilian city

# In[27]:

data = br_cities[br_cities['status_code'] == 404].copy().reset_index(drop=True)
data


# There are some cities that we already know that have a page with transparency and open data but the pattern is different from the one above.
# 
# Second Pattern: `cm{city}-{state}.portaltp.com.br`

# In[28]:

portal_url = 'https://cm{}-{}.portaltp.com.br/'
data['transparency_portal_url'] = data.apply(lambda row: portal_url.format(
                                                                           row['normalized_name'],
                                                                           row['state']), axis=1)
data


# We still need to update the status code column

# In[29]:

get_ipython().run_cell_magic('time', '', "data.loc[:,'status_code'] = data.apply(lambda x: get_status(x['transparency_portal_url']), axis=1)")


# In[30]:

data


# In[31]:

# study purposes
data.loc[8, 'status_code'] = 200
data


# In[32]:

data.loc[data['status_code'] == 404, 'transparency_portal_url'] = None
data


# In[33]:

br_cities.loc[br_cities['status_code'] == 404, 'transparency_portal_url'] = None
br_cities


# In[34]:

unnecessary_columns = ['normalized_name', 'status_code']
br_cities = pd.merge(br_cities.drop(unnecessary_columns, axis=1),
                  data.drop(unnecessary_columns, axis=1),
                  on=['code', 'name', 'state'], how='left')

br_cities['transparency_portal_url'] = br_cities       .apply(lambda row: row['transparency_portal_url_x'] or row['transparency_portal_url_y'], axis=1)
    
unnecessary_columns = ['transparency_portal_url_x', 'transparency_portal_url_y']
br_cities = br_cities.drop(unnecessary_columns, axis=1)
br_cities


# # Conclusions
# 
# After all that study, we find that in that pattern of transparency portals list there are already 279 cities, from them 19 are returning an Internal Server Error (Status Code: 5XX).
# 
# It is something like 5% of all Brazilian existing cities!
# 
# Below we have a table with all those cities with portals ;)

# In[35]:

with_tp_portal = pd.read_csv('../data/2017-05-30-cities_with_tp_portal.csv')
with_tp_portal.shape


# In[36]:

with_tp_portal

