
# coding: utf-8

# # Introductory Data Exploration of Brazilian Cities
# In this dataset we have a population projection for each Brazilian city in the year of 2013.
# 
# 

# In[1]:

import pandas as pd
import numpy as np


cities = pd.read_excel('../data/Cidades - estimativa 2013.xlsx',
                       dtype={'COD. UF': np.str, 'COD. MUNIC': str},
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


# In[ ]:




# In[ ]:



