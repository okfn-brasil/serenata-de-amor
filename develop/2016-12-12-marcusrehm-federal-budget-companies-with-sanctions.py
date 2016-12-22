
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np


# ### Amendments with Federal Budget

# In[50]:

amendments = pd.read_csv('../data/2016-12-22-amendments.xz', dtype={'proposal_id': np.str,
                                                                   'amendment_beneficiary': np.str,
                                                                   'amendment_program_code': np.str,
                                                                   'amendment_proposal_tranfer_value': np.float,
                                                                   'amendment_tranfer_value': np.float})
amendments.fillna('', inplace=True)
amendments.shape


# In[51]:

amendments.iloc[0]


# ### Agreements made with Federal Budget

# In[124]:

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


# #### Agreements related to amendments

# In[125]:

agreements_with_amendments = agreements.merge(amendments, on='proposal_id')
agreements_with_amendments = agreements_with_amendments.filter(['amendment_number', 'congressperson_name', 
                                                                'amendment_beneficiary','date_signed', 
                                                                'agreement_end_date', 'agreement_number', 
                                                                'situation'])
agreements_with_amendments.iloc[0]


# ### Impeded Non-Profit Entities
# 
# This dataset gather Non-profit private entities that are prevented from entering into agreements, onlending agreements or terms of partnership with the federal public administration.
# 
# Origin of the information: Controladoria-Geral da União - CGU (Comptroller General of the Union)

# In[57]:

impeded_non_profit_entities = pd.read_csv('../data/2016-12-20-impeded-non-profit-entities.xz', 
                                              dtype={'company_cnpj': np.str,
                                                     'agreement_number': np.str})
impeded_non_profit_entities.shape


# In[58]:

impeded_non_profit_entities.iloc[0]


# #### First we need to get the agreement in which entities were impeded:

# In[126]:

impeded_entities_w_start_date = agreements_with_amendments.filter(['amendment_beneficiary', 
                                                                   'agreement_number', 
                                                                   'agreement_end_date']
                                                                       ).merge(impeded_non_profit_entities, 
                                                                               left_on=(['amendment_beneficiary', 
                                                                                         'agreement_number']), 
                                                                               right_on=(['company_cnpj', 
                                                                                          'agreement_number'])
                                                                        ).filter(['company_cnpj',
                                                                                 'compay_name',
                                                                                 'agreement_number',
                                                                                 'agreement_end_date',
                                                                                 'grating_body',
                                                                                 'impediment_reason'])

impeded_entities_w_start_date = impeded_entities_w_start_date.rename(columns = 
                                                                     {'agreement_end_date':'date_impended', 
                                                                      'agreement_number': 'impended_agreement'})
impeded_entities_w_start_date.iloc[0]


# Because the dataset doesn't gives the date when the entity becomes impended, we are are using the end date of the agreement where the entity was impended as a minimum date called here as **date_impended**.
# 
# So **date_impended** means that we are concerned only with agreements signed after this date.

# In[130]:

agreements_after_impended = agreements_with_amendments.merge(impeded_entities_w_start_date, 
                                                                   left_on=(['amendment_beneficiary']), 
                                                                   right_on=(['company_cnpj']))


# #### Now we can query the agreements signed after the entities were impended
# 
# Below we have a list of agreements that are still in execution and are related to the amendments that have as beneficiaries non-profit entities that are impeded. In addition, the difference between the date of signature of the agreements in execution and the date of entities disability is less than 2 years.

# In[131]:

agreements_after_impended.query('situation == \'Em execução\' and                                  date_impended < date_signed and                                  date_signed.dt.year - date_impended.dt.year < 2')


# ### Inident and Suspended Companies
# 
# This dataset gather companies and individuals who have suffered sanctions by the organs and entities of the public administration of the various federative spheres.
# 
# Origin of the information: Controladoria-Geral da União - CGU (Comptroller General of the Union)

# In[25]:

inident_and_suspended_companies = pd.read_csv('../data/2016-12-21-inident-and-suspended-companies.xz',
                                              dtype={'sanctioned_cnpj_cpf': np.str,
                                                     'process_number': np.str},
                                              parse_dates = ['sanction_start_date','sanction_end_date', 
                                                             'data_source_date', 'published_date'], 
                                              low_memory=False)
inident_and_suspended_companies.fillna('', inplace=True)
inident_and_suspended_companies['sanction_start_date'] = pd.to_datetime(inident_and_suspended_companies['sanction_start_date'], format='%Y-%m-%d')
inident_and_suspended_companies['sanction_end_date'] = pd.to_datetime(inident_and_suspended_companies['sanction_end_date'], format='%Y-%m-%d')
inident_and_suspended_companies.shape


# In[37]:

inident_and_suspended_companies.iloc[0]


# In[219]:

agreements_with_suspended_companies = agreements_with_amendments.merge(inident_and_suspended_companies, 
                                                                   left_on='amendment_beneficiary', 
                                                                   right_on='sanctioned_cnpj_cpf')


# In[229]:

agreements_with_suspended_companies.query('SIT_CONVENIO == \'Em execução\' and                                             sanction_start_date <= DIA_ASSIN_CONV and                                             DIA_ASSIN_CONV <= sanction_end_date')

