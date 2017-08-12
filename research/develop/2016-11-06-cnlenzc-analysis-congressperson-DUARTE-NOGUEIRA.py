
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


# # agrupa todas as despesas de viagem do deputado DUARTE NOGUEIRA

# In[3]:

data_filtro = data[((data.applicant_id ==1816) & (data.subquota_number == 999))]

tot = data_filtro.groupby(['state', 'party', 'congressperson_name', 'supplier', 'passenger', 'leg_of_the_trip', 'month']).aggregate({'total_net_value': np.sum})

tot.unstack(-1).head(100)


# # agrupa todas as despesas do deputado DUARTE NOGUEIRA

# In[4]:

data_filtro = data[((data.applicant_id ==1816) & (1==1))]

tot = data_filtro.groupby(['state', 'party', 'congressperson_name', 'subquota_description', 'supplier', 'month']).aggregate({'total_net_value': np.sum})

tot.unstack(-1).head(100)


# In[ ]:



