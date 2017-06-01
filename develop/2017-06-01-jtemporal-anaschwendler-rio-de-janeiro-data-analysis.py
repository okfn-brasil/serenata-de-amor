
# coding: utf-8

# # Rio de Janeiro data study
# 
# With this notebook we aim to assess whether Rio de Janeiro's data is ready to be used.
# Documentation on Rio's data used in this notebook can be found [here](http://dadosabertos.rio.rj.gov.br/apiRioTransparente/apresentacao/pdf/documentacao_despesas.pdf).

# In[6]:

from urllib.request import urlretrieve
import pandas as pd


data_url = 'http://dadosabertos2.rio.rj.gov.br/dadoaberto/ws/riotransparente/csv/despesa/2016'

file_path = '../data/riotransparente.csv'

urlretrieve(data_url, file_path)
data = pd.read_csv(file_path)


# In[7]:

data.head()


# In[8]:

data.iloc[0]


# There is no way to identify which person/company provided the service for the city

# ### Conclusion
# At first look there isn't much usable data. There's no CNPJ, nor reimbursements, or value spent.
#  
# We could ask for: reimbursements images, CNPJ from the hired company, expense.
#  
# Also we noted there were test data online which doesn't give much credit to the data that is on the site.
#  
# We couldn't find information on expenses made on food, airplane tickets and hotels.
