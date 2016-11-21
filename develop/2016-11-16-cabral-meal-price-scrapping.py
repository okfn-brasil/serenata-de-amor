
# coding: utf-8

# In[38]:

get_ipython().magic('matplotlib notebook')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statistics import mean
import re
#For scrapping usage
from urllib.request import urlopen
from bs4 import BeautifulSoup



# In[2]:

#using just one hard coded URL for runnung tests
place = "https://www.tripadvisor.com/Restaurant_Review-g303322-d2347734-Reviews-Coco_Bambu_Lago_Sul-Brasilia_Federal_District.html"
page = urlopen(place)
soup = BeautifulSoup(page)


# In[3]:

#To check the URL strutcture
#too long, commented it
#print (soup.prettify)


# In[4]:

print (soup.title)


# In[5]:

print (soup.div)


# In[6]:

#soup.find_all("div")
#Found out too many divs


# In[20]:

pricetag = soup.find("div", { "class" : "detail first price_rating separator" })


# In[21]:

pricetag = pricetag.string.strip()


# In[22]:

pricetag


# In[23]:

#Transforming price tag in intergers 

def translate_symbol_to_numeral(pricetag): 
    pricetag = pricetag.replace(' ', '')
    tags = pricetag.split('-')
    tags = list(map(lambda x : len(x), tags))
    if len(tags) == 1:
        return tags[0]
    else:
        return mean(tags)
pricetag = translate_symbol_to_numeral(pricetag)
print (pricetag)
    


# ## Sourcing the meal places

# In[26]:

data = pd.read_csv('../data/2016-08-08-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# In[27]:

meals = data[data.subquota_description == 'Congressperson meal']


# In[28]:

grouped = meals.groupby('cnpj_cpf', as_index=False)

print('{} total cnpj/cpfs, {} are unique'.format(len(meals), len(grouped)))


# 
# ## Creating a dataframe with the first supplier name for each cnpj_cpf:
# 

# In[14]:

cnpj_cpfs = []
names = []
for group in grouped:
    cnpj_cpfs.append(group[0])
    names.append(group[1].iloc[0].supplier)

names = pd.DataFrame({'cnpj_cpf': cnpj_cpfs, 'supplier_name': names})
names.head()


# ## Isolating the supplier model 

# In[15]:

coco_bambu = names.loc[names['supplier_name'] == 'COCO BAMBU LAGO SUL COMERCIO DE ALIMENTOS LTDA.']


# In[16]:

coco_bambu


# ## Adding pricetag to the DF

# In[17]:

coco_bambu['price_range'] = pricetag


# In[18]:

coco_bambu


# ## Sourcing Companies dataset
# ### Will compare CNPJ numbers and retrieve name and fantasy name for future research

# In[35]:

companies = pd.read_csv('../data/2016-09-03-companies.xz', dtype={'trade_name': np.str})


# In[36]:

companies.iloc[0]


# In[49]:

def cleanup_cnpj(cnpj):
    # print(type(cnpj))
    regex = r'\d'
    digits = re.findall(regex, cnpj)
    return ''.join(digits)

cleanup_cnpj('89344324.3241-323')


# In[50]:

companies['cleaned_cnpj'] = companies['cnpj'].map(cleanup_cnpj)
companies.iloc[0]


# In[60]:

congressperson_meal_companies = companies[companies['cleaned_cnpj'].isin(names['cnpj_cpf'])]
# a_dataset[a_dataset['cnpj'].isin(another_data['cnpj])]
congressperson_meal_companies.shape


# Default Tripadivsor URL for study purpose
# https://www.tripadvisor.com/Search?geo=303322&pid=3826&typeaheadRedirect=true&redirect=&startTime=1479311838571&uiOrigin=MASTHEAD&q=coco+bambu&returnTo=__2F__Restaurant__5F__Review__2D__g303322__2D__d2347734__2D__Reviews__2D__Coco__5F__Bambu__5F__Lago__5F__Sul__2D__Brasilia__5F__Federal__5F__District__2E__html&searchSessionId=882DF6A9A9540BDAD8FD36432D65D45B1479311256604ssid
# 
# https://www.tripadvisor.com/Search?geo=294280&redirect&q=COCO+BAMBU+FRUTOS+DO+MAR&uiOrigin=MASTHEAD&ssrc=e&typeaheadRedirect=true&returnTo=__2F__Restaurant__5F__Review__2D__g303322__2D__d2347734__2D__Reviews__2D__Coco__5F__Bambu__5F__Lago__5F__Sul__2D__Brasilia__5F__Federal__5F__District__2E__html&pid=3825&startTime=undefined&searchSessionId=882DF6A9A9540BDAD8FD36432D65D45B1479314836242ssid

# In[64]:

congressperson_meal_companies[congressperson_meal_companies['cleaned_cnpj'] == '10542662000147'].iloc[0]


# In[ ]:



