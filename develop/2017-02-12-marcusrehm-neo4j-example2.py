
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np


# ### Amendments with Federal Budget

# In[2]:

amendments = pd.read_csv('../data/2016-12-22-amendments.xz', 
                         dtype={'proposal_id': np.str,
                               'amendment_beneficiary': np.str,
                               'amendment_program_code': np.str,
                               'amendment_proposal_tranfer_value': np.float,
                               'amendment_tranfer_value': np.float})
amendments.fillna('', inplace=True)
amendments.shape


# ### Agreements made with Federal Budget

# In[3]:

agreements = pd.read_csv('../data/2016-12-22-agreements.xz', 
                         usecols=(['agreement_number', 'proposal_id', 
                                   'agreement_end_date','date_signed', 'situation']),
                         dtype={'agreement_number': np.str, 
                                'proposal_id': np.str,
                                'situation': np.str}, 
                         parse_dates=['agreement_end_date', 'date_signed'],
                         low_memory=False)
agreements.fillna('', inplace=True)
agreements.shape


# ### Agreements related to amendments

# In[4]:

agreements_with_amendments = agreements.merge(amendments, on='proposal_id')
agreements_with_amendments = agreements_with_amendments.filter(['amendment_number', 
                                                                'congressperson_name', 
                                                                'amendment_beneficiary',
                                                                'date_signed', 
                                                                'agreement_end_date',
                                                                'agreement_number', 
                                                                'situation'])
agreements_with_amendments.shape


# ---
# ## Impeded Non-Profit Entities - CEPIM
# 
# This dataset gather Non-profit entities that are prevented from entering into agreements, onlending agreements or terms of partnership with the federal public administration.
# 
# Origin of the information: Controladoria-Geral da União - CGU (Comptroller General of the Union)

# In[5]:

impeded_non_profit_entities = pd.read_csv('../data/2016-12-20-impeded-non-profit-entities.xz', 
                                              dtype={'company_cnpj': np.str,
                                                     'agreement_number': np.str})
impeded_non_profit_entities.shape


# 
# First we need to get the agreements in which entities were impeded:

# In[6]:

impeded_entities_w_start_date = agreements_with_amendments.merge(
                                    impeded_non_profit_entities, 
                                    left_on=(['amendment_beneficiary', 
                                              'agreement_number']), 
                                    right_on=(['company_cnpj', 
                                               'agreement_number']))

impeded_entities_w_start_date = impeded_entities_w_start_date.filter(['company_cnpj',
                                                                     'compay_name',
                                                                     'agreement_number',
                                                                     'agreement_end_date',
                                                                     'grating_body',
                                                                     'impediment_reason'])

impeded_entities_w_start_date = impeded_entities_w_start_date.rename(columns = 
                                             {'agreement_end_date':'date_impended', 
                                              'agreement_number': 'impended_agreement'})
impeded_entities_w_start_date.iloc[0]


# Because the dataset doesn't gives the date when the entity becomes impended, we are using the end date of the agreement where the entity was impended as a minimum date called here as **date_impended**.
# 
# So **date_impended** means that we are concerned only with agreements signed after this date.

# In[7]:

agreements_after_impended = agreements_with_amendments.merge(
                                        impeded_entities_w_start_date, 
                                        left_on=(['amendment_beneficiary']), 
                                        right_on=(['company_cnpj']))


# #### Querying the agreements signed after the entities were impended
# 
# Below we have a list of agreements that are still in execution and are related to the amendments that have as beneficiaries non-profit entities that are impeded. In addition, the difference between the date of signature of the agreements in execution and the date of entities disability is less than 2 years.

# In[8]:

agreements_after_impended = agreements_after_impended.query(
                                    'situation == \'Em execução\' and \
                                     date_impended < date_signed and \
                                     date_signed.dt.year - date_impended.dt.year < 2')
agreements_after_impended.shape


# In[9]:

agreements_after_impended


# In[21]:

from py2neo import Node
from py2neo import Relationship
from py2neo import Graph

graph = Graph()
graph.delete_all()

congresspersons = [Node("Congressperson", name=congressperson) 
                   for congressperson in 
                   agreements_after_impended['congressperson_name'].unique()]
entities = [Node("Entity", name=beneficiary) 
            for beneficiary in 
            agreements_after_impended['compay_name'].unique()]

for congressperson in congresspersons:
    graph.create(congressperson)

for entity in entities:
    graph.create(entity)

for index, row in agreements_after_impended.iterrows():
    congressperson = list(filter(lambda c: c['name'] == row['congressperson_name'], 
                                 congresspersons))[0]
    entity = list(filter(lambda c: c['name'] == row['compay_name'], 
                         entities))[0]
    graph.create(Relationship(congressperson, 
                              "benefited", 
                              entity))


# In[25]:

import neo4jupyter

neo4jupyter.init_notebook_mode()


# In[27]:

from neo4jupyter import draw

options = {"Congressperson": "name", "Entity": "name"}
draw(graph, options)


# In[ ]:



