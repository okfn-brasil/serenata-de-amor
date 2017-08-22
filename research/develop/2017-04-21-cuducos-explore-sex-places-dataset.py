
# coding: utf-8

# # Exploring the first version of Sex Place Distances dataset

# This notebook plays around with data from the first version of the dataset `data/2017-04-21-sex-place-distance.xz`. This first version collected data about companies:
# 
# * In one of these cities: BOA VISTA, CURVELO, SANTA CRUZ DO SUL, PORTO ALEGRE, SAO JOSE DOS PINHAIS, SETE LAGOAS, BOITUVA, IPATINGA, UBERABA, CONGONHAS, SOROCABA, PARAOPEBA, CHAPECO, CUIABA, SALVADOR, BAURU and LAJEADO
# * Where expenses with a total net value equal or higher than 100 BRL
# * In which congresspeople from the 2015 term have expend public money
# 
# The set of cities was taken [random sample that sounded promosing](https://twitter.com/cuducos/status/840882495868530688)… but hold your horses: further analysis is disapointing… let's get started.

# In[1]:

import numpy as np
import pandas as pd
from serenata_toolbox.datasets import fetch

DTYPE = dict(cnpj=np.str, cnpj_cpf=np.str)


# In[2]:

fetch('2017-04-21-sex-place-distances.xz', '../data')


# In[3]:

companies = pd.read_csv('../data/2016-09-03-companies.xz', dtype=DTYPE, low_memory=False)
companies.cnpj = companies.cnpj.str.replace(r'\D', '')
companies.shape


# In[4]:

sex_places = pd.read_csv('../data/2017-04-21-sex-place-distances.xz', dtype=DTYPE)
sex_places.shape


# This dataset has all sort of ditances between companies and the closest sex place:

# In[5]:

sex_places.distance.describe()


# ## Sex places _close enough_ to places in which congresspeople were
# 
# From this sample (n=2245) 81 places are at least 3m away from the venue in which at least a congressperson made an expense since 2015:

# In[6]:

close_enough = sex_places.query('distance < 3')
close_enough.shape


# In[7]:

close_enough.head()


# ## Taking a closer look
# 
# Let's generate some Jarbas links to take a closer look at them!

# In[8]:

link = 'https://jarbas.serenatadeamor.org/#/cnpjCpf/{}'
cnpjs = (place.cnpj for _, place in close_enough.iterrows())
for cnpj in cnpjs:
    print(link.format(cnpj))


# ### Villa Gorini
# 
# Two CNPJs were assigned to a night club called Villa Gorini:

# In[9]:

close_enough[close_enough.cnpj == '03874976000181'].iloc[0]


# In[10]:

close_enough[close_enough.cnpj == '17084369000122'].iloc[0]


# However the point here is that Google Places API seems rather imprecise when looking for an address that has a KM instead of a street number:

# In[11]:

companies[companies.cnpj == '03874976000181'].iloc[0].address


# In[12]:

companies[companies.cnpj == '17084369000122'].iloc[0].address


# And actually Villa Gorini [is at KM 701](https://encrypted.google.com/search?q=villa%20gorini) (not 480, for instance).

# ### Yume Espaço Terapêutico
# 
# [Yume Espaço Terapêutico](https://jarbas.serenatadeamor.org/#/cnpjCpf/14310257000154) is another example of a false positive.

# In[13]:

close_enough.iloc[66]


# The company _SETE QUATRO COMUNICACAO E PUBLICIDADE LTDA - EPP_ is clearly in a [office building](https://goo.gl/maps/k6z8bdHLVxR2), probably the same building in which _Yume Espaço Terapêutico_ offers their service.

# ### Céu Azul Motel
# 
# Finally [CONTRASTE EDITORA E INDUSTRIA GRAFICA EIRELI](https://jarbas.serenatadeamor.org/#/cnpjCpf/33867664000101) has very appealling picures in Jarbas (actually in Google Street View). 

# In[14]:

close_enough.iloc[-1]


# However a [Google Maps search](https://www.google.com/maps/place/R.+Bar%C3%A3o+de+Maca%C3%BAbas,+27+-+Barbalho,+Salvador+-+BA,+40302-000,+Brazil/@-12.96636,-38.4996147,17z/data=!3m1!4b1!4m5!3m4!1s0x71604d877430fb3:0x2e71207287112e18!8m2!3d-12.96636!4d-38.497426?hl=en) shows that there is actually a press **and** a motel at this address.

# ## Final considerations
# 
# So far the attemp to fetch sex places has brought mainly false positives. We need to improve our methods to make it worth it to implement this hypothesis further.
