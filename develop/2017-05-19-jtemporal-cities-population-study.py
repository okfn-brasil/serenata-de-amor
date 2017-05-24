
# coding: utf-8

# # Introductory Data Exploration of Brazilian Cities
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


# In[10]:

from serenata_toolbox.datasets import fetch

fetch('2017-05-22-brazilian-cities.csv', '../data')


# In[11]:

# csv generated with https://github.com/cuducos/brazilian-cities
brazilian_cities = pd.read_csv('../data/2017-05-22-brazilian-cities.csv')
brazilian_cities.head()


# In[12]:

brazilian_cities.shape


# In[13]:

brazilian_cities['state'] = brazilian_cities['state'].apply(lambda x: x.lower())


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
# There are some cities that we already know that have a page with transparency and open data. The main object here is to find how many cities have that.
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

colatina = brazilian_cities[brazilian_cities['code'] == 320150]['transparency_portal_url'].values[0]
statusOK = get_status(colatina)

abaete = brazilian_cities[brazilian_cities['code'] == 310020]['transparency_portal_url'].values[0]
statusNOK = get_status(abaete)


# In[20]:

br_cities = brazilian_cities.loc[:10,:].copy()
br_cities.loc[:,'status_code'] = br_cities.apply(lambda x: get_status(x['transparency_portal_url']), axis=1)


# In[21]:

br_cities


# This will take too long considering we have 5570 cities to address.

# In[22]:

def get_status(url):
    try:
        return requests.head(url).status_code
    except requests.ConnectionError:
        return 404


# With that in mind, the medicine is patience. The following cell will take a long time to run so get a cup of coffee ;)

# In[23]:

brazilian_cities['status_code'] = brazilian_cities['transparency_portal_url'].apply(lambda x: get_status(x))


# In[25]:

brazilian_cities.head(10)


# Let's try using grequests.
# 
# I know that we can find two different status code in the first 10 cities urls test. So let's use those 10 to test grequests ;)

# In[26]:

import grequests

rs = (grequests.get(u) for u in list(br_cities['transparency_portal_url']))


# In[27]:

def exception_handler(request, exception):
    return 404

responses = grequests.map(rs, exception_handler=exception_handler)


# In[28]:

codes = [int(x) for x in br_cities['status_code'].values]

print(pd.unique(codes), pd.unique(responses))


# In[29]:

responses


# The result above got me wondering where were those 200 statuses code we've seen before. I tested the code on the command line and they are there. So a little reasearch and I found that apparently it is not possible to run async tasks easily on a jupyter notebook [ref](http://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Asynchronous.html).

# In[38]:

data = brazilian_cities[brazilian_cities['status_code'] == 200]
data = data.reset_index()
data.head()


# In[39]:

data.shape


# In[42]:

data.to_csv('../data/cities-with-tp-url.xz', compression='xz', index=False)


# In[ ]:



