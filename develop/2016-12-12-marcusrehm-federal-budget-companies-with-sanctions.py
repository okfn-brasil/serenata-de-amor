
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


# In[3]:

amendments.iloc[0]


# ### Agreements made with Federal Budget

# In[4]:

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


# In[5]:

agreements.iloc[0]


# ### Agreements related to amendments

# In[6]:

agreements_with_amendments = agreements.merge(amendments, on='proposal_id')
agreements_with_amendments = agreements_with_amendments.filter(['amendment_number', 
                                                                'congressperson_name', 
                                                                'amendment_beneficiary',
                                                                'date_signed', 
                                                                'agreement_end_date',
                                                                'agreement_number', 
                                                                'situation'])
agreements_with_amendments.shape


# In[7]:

agreements_with_amendments.iloc[0]


# ---
# ## Impeded Non-Profit Entities - CEPIM
# 
# This dataset gather Non-profit entities that are prevented from entering into agreements, onlending agreements or terms of partnership with the federal public administration.
# 
# Origin of the information: Controladoria-Geral da União - CGU (Comptroller General of the Union)

# In[8]:

impeded_non_profit_entities = pd.read_csv('../data/2016-12-20-impeded-non-profit-entities.xz', 
                                              dtype={'company_cnpj': np.str,
                                                     'agreement_number': np.str})
impeded_non_profit_entities.shape


# In[9]:

impeded_non_profit_entities.iloc[0]


# 
# First we need to get the agreements in which entities were impeded:

# In[10]:

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

# In[11]:

agreements_after_impended = agreements_with_amendments.merge(
                                        impeded_entities_w_start_date, 
                                        left_on=(['amendment_beneficiary']), 
                                        right_on=(['company_cnpj']))


# #### Querying the agreements signed after the entities were impended
# 
# Below we have a list of agreements that are still in execution and are related to the amendments that have as beneficiaries non-profit entities that are impeded. In addition, the difference between the date of signature of the agreements in execution and the date of entities disability is less than 2 years.

# In[12]:

agreements_after_impended.query('situation == \'Em execução\' and                                  date_impended < date_signed and                                  date_signed.dt.year - date_impended.dt.year < 2').shape


# In[13]:

agreements_after_impended.query('situation == \'Em execução\' and                                  date_impended < date_signed and                                  date_signed.dt.year - date_impended.dt.year < 2')


# ---
# ## Inident and Suspended Companies - CEIS
# 
# This dataset gather companies and individuals who have suffered sanctions by the organs and entities of the public administration of the various federative spheres.
# 
# Origin of the information: Controladoria-Geral da União - CGU (Comptroller General of the Union)

# In[14]:

inident_and_suspended_companies = pd.read_csv('../data/2016-12-21-inident-and-suspended-companies.xz',
                                              dtype={'sanctioned_cnpj_cpf': np.str,
                                                     'process_number': np.str},
                                              parse_dates = ['sanction_start_date',
                                                             'sanction_end_date', 
                                                             'data_source_date',
                                                             'published_date'], 
                                              low_memory=False)
inident_and_suspended_companies.fillna('', inplace=True)
inident_and_suspended_companies['sanction_start_date'] = pd.to_datetime(
                            inident_and_suspended_companies['sanction_start_date'], 
                            format='%Y-%m-%d')
inident_and_suspended_companies['sanction_end_date'] = pd.to_datetime(
                            inident_and_suspended_companies['sanction_end_date'],
                            format='%Y-%m-%d')
inident_and_suspended_companies.shape


# In[15]:

inident_and_suspended_companies.iloc[0]


# In[16]:

agreements_with_suspended_companies = agreements_with_amendments.merge(
                                        inident_and_suspended_companies, 
                                        left_on='amendment_beneficiary', 
                                        right_on='sanctioned_cnpj_cpf')
agreements_with_suspended_companies.shape


# #### Querying the agreements still running after entities were suspended
# 
# Below we have a list of agreements that are still in execution and which the signed date are between sanction's start and end date.

# In[17]:

agreements_with_suspended_companies.query('entity_type == \'Juridica\' and                                            situation == \'Em execução\' and                                            sanction_start_date <= date_signed and                                            date_signed <= sanction_end_date'
                                         ).shape


# In[18]:

agreements_with_suspended_companies = agreements_with_suspended_companies.rename(
                                        columns = {'date_signed':'agreement_date_signed'})


# In[19]:

agreements_with_suspended_companies.query('entity_type == \'Juridica\' and                                           situation == \'Em execução\' and                                           sanction_start_date <= agreement_date_signed and                                           agreement_date_signed <= sanction_end_date'
                                         ).filter(['amendment_number',
                                                   'agreement_number',
                                                   'congressperson_name',
                                                   'sanctioned_cnpj_cpf',
                                                   'name_given_by_sanctioning_body',
                                                   'company_name_receita_database',
                                                   'trading_name_receita_database',
                                                   'process_number',
                                                   'agreement_date_signed',
                                                   'sanction_start_date',
                                                   'sanction_end_date',
                                                   'sanction_type',
                                                   'sanctioning_body',
                                                   'state_of_sanctioning_body',
                                                   'data_source',
                                                   'data_source_date',
                                                   'published_date'])


# ---
# ## National Registry of Punished Companies - CNEP
# 
# The National Register of Punished Companies (CNEP) is an information bank maintained by the Federal Comptroller's Office (CGU), whose purpose is to consolidate the relationship of companies that have suffered any of the punishments provided in Law 12,846 / 2013 (Anti-Corruption Law).
# 
# Origin of the information: Controladoria-Geral da União - CGU (Comptroller General of the Union)

# In[20]:

punished_companies = pd.read_csv('../data/2016-12-21-national-register-punished-companies.xz',
                                              dtype={'sanctioned_cnpj_cpf': np.str,
                                                     'process_number': np.str},
                                              parse_dates = ['sanction_start_date',
                                                             'sanction_end_date', 
                                                             'data_source_date',
                                                             'published_date'], 
                                              low_memory=False)
punished_companies.fillna('', inplace=True)
punished_companies.shape


# In[21]:

len(punished_companies['sanctioned_cnpj_cpf'].unique())


# As we can see above, this dataset has only 9 records listed and 8 companies. 

# In[22]:

punished_companies.iloc[0]


# Here we got the agreements related to these punished companies:

# In[23]:

agreements_with_punished_companies = agreements_with_amendments.merge(
                                        punished_companies, 
                                        left_on='amendment_beneficiary', 
                                        right_on='sanctioned_cnpj_cpf')
agreements_with_punished_companies.shape


# As of 12/21/2016 there are no agreements related to these punished companies.
