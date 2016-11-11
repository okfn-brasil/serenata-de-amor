
# coding: utf-8

# In[2]:

import pandas as pd
import numpy as np


# In[40]:

data = pd.read_csv('../data/2016-08-08-current-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# # agrupa todas as despesas de viagem do deputado DUARTE NOGUEIRA

# In[82]:

data_filtro = data[((data.applicant_id ==1816) & (data.subquota_number == 999))]

tot = data_filtro.groupby(['state', 'party', 'congressperson_name', 'supplier', 'passenger', 'leg_of_the_trip', 'month']).aggregate({'net_value': np.sum})

tot.unstack(-1).head(100)


# # agrupa todas as despesas do deputado DUARTE NOGUEIRA

# In[81]:

data_filtro = data[((data.applicant_id ==1816) & (1==1))]

tot = data_filtro.groupby(['state', 'party', 'congressperson_name', 'subquota_description', 'supplier', 'month']).aggregate({'net_value': np.sum})

tot.unstack(-1).head(100)

