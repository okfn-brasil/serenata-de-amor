
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np


# In[2]:

data = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str},
                   low_memory=False)
data = data[data['year'] == 2016]


# # analise de despesas por deputado X categoria

# In[3]:

data_filtro = data[((data.party == 'PT') | (data.party == 'PMDB') | (data.party == 'PSDB'))& ((data.state == 'SP') | (data.state == 'RJ'))& ((data.subquota_number == 5) | (data.subquota_number == 999) | (data.subquota_number == 120) | (data.subquota_number == 13))]

tot = data_filtro.groupby(['party', 'state', 'applicant_id', 'congressperson_name', 'subquota_description']).aggregate({'total_net_value': np.sum})

tot.unstack(-1)


# In[4]:

data_filtro = data[(data.subquota_number == 999)]

tot =    data_filtro.groupby(['party', 'state', 'congressperson_name', 'subquota_description', 'month'])   .aggregate({'total_net_value': np.sum})

tot.unstack()


# In[5]:

data_filtro = data[(data.subquota_number == 999)]

tot =    data_filtro.groupby(['cnpj_cpf', 'supplier', 'subquota_description', 'month'])   .aggregate({'total_net_value': np.sum})

tot.unstack()

