
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np


# ## Reimbursements
# 
# This notebook crosses the **CEIS** dataset which gather companies with some type of problem with Federal spheres and reimbursements related to **CEAP**.

# In[2]:

reimbursements = pd.read_csv('../data/2016-08-08-current-year.xz',
                                              dtype={'cnpj_cpf': np.str,
                                                     'document_id': np.str,
                                                     'reimbursement_value': np.float},
                                              parse_dates = ['issue_date'], 
                                              low_memory=False)
reimbursements.shape


# In[3]:

reimbursements.iloc[1]


# ---
# ## Inident and Suspended Companies - CEIS
# 
# This dataset gather companies and individuals who have suffered sanctions by the organs and entities of the public administration of the various federative spheres.
# 
# Origin of the information: Controladoria-Geral da União - CGU (Comptroller General of the Union)

# In[4]:

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


# In[5]:

inident_and_suspended_companies.iloc[0]


# #### Querying the reimbursements from companies suspended
# 
# Below we have a list of reibursements from dates where the suplier is listed in CEIS dataset.

# In[6]:

reimbursements_from_inident_companies = reimbursements.merge(
                                        inident_and_suspended_companies, 
                                        left_on='cnpj_cpf', 
                                        right_on='sanctioned_cnpj_cpf')
reimbursements_from_inident_companies.shape


# Now from the selected reimbursements, we get only the ones made between time the saction is valid.

# In[7]:

suspect_reimbursements = reimbursements_from_inident_companies.query(
                                           'sanction_start_date <= issue_date and \
                                           issue_date <= sanction_end_date')
suspect_reimbursements.shape


# In[8]:

suspect_reimbursements.filter([ 'document_id',
                                'congressperson_name',
                                'congressperson_id',
                                'congressperson_document',
                                'term',
                                'subquota_description',
                                'subquota_group_description',
                                'supplier',
                                'cnpj_cpf',
                                'document_number',
                                'document_type',
                                'issue_date',
                                'document_value',
                                'name_given_by_sanctioning_body',
                                'company_name_receita_database', 
                                'trading_name_receita_database',
                                'process_number', 
                                'sanction_type', 
                                'sanction_start_date',
                                'sanction_end_date', 
                                'sanctioning_body'])


# The study above doesnt prove anything ilegal, but at least the congressperson should have research about the company before use its services.
