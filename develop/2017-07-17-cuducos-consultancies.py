
# coding: utf-8

# # Exploratory analysis on CEAP consultancies

# The idea of this notebook is to offer an overview of congresspeople expenses with consultancies. It's simpler than a proper exploratory analysis, but I hope this help and encourage more analysis related to this subquota.
# 
# Let's get started by loading the data we have about the reimbursements:

# In[1]:

import numpy as np
import pandas as pd


reimbursements = pd.read_csv(
    '../data/2016-11-19-reimbursements.xz',
    dtype={'cnpj_cpf': np.str},
    low_memory=False
)
reimbursements.shape


# A quick look in all subquotas just to make sure we pickup the right one when filtering expenses with consultancies:

# In[2]:

keys = ['subquota_number', 'subquota_description']
reimbursements[keys].groupby(keys).count().reset_index()


# In[3]:

consultancies = reimbursements[reimbursements.subquota_number == 4]
consultancies.shape


# ## Counting where congresspeople spend on consultancy

# This first grouping looks into cases in which a congressperson has many expenses with consultancies, but all/most of them are made in the very same company.
# 
# First lets see how many different reimbursements each congressperson had for each consultancy.

# In[4]:

cols = ['applicant_id', 'congressperson_name', 'cnpj_cpf']
count_per_consultancy = consultancies[cols]             .groupby(cols)             .size()             .to_frame('count_per_consultancy')             .reset_index()             .sort_values('count_per_consultancy', ascending=False)
count_per_consultancy.head()


# ## Counting the total reimbursements congresspeople had in consultancies
# 
# Now let's see the total reimbursements for all consultancies per congresspeople.

# In[5]:

cols = ['applicant_id']
consultancies_count = consultancies.groupby('applicant_id')                         .size()                         .to_frame('total_consultancies')                         .reset_index()                         .sort_values('total_consultancies', ascending=False)
consultancies_count.head()


# ## Find congressperson loyal to a specific consultancy

# In[6]:

consultancies_grouped = count_per_consultancy.merge(consultancies_count)
consultancies_grouped['percentage'] =     consultancies_grouped.count_per_consultancy / consultancies_grouped.total_consultancies
consultancies_grouped.sort_values('percentage', ascending=False)


# This results aren't so helpful, so let's use a minimun of 10 consultancies expenses at the same company, and a ratio of 80% of consultancies expenses done at this same company:

# In[7]:

results = consultancies_grouped     .query('count_per_consultancy >= 10')     .query('percentage >= 0.8')
results


# There are 126 congressperson that are constantly using the same consultancy. This is **not** illegal _per se_ but might be an indicator of something. If anyone wanna go deeper, here are the Jarbas links for each of this cases:

# In[8]:

def jarbas_link(row):
    base_url = (
        'https://jarbas.serenatadeamor.org/#/'
        'applicantId/{applicant_id}/'
        'cnpjCpf/{cnpj_cpf}/'
        'subquotaId/4'
    )
    url = str(base_url.format(**row))
    return '<a href="{}">Jarbas</a>'.format(url)

results['url'] = results.apply(jarbas_link, axis=1)
links = results[[
    'congressperson_name',
    'count_per_consultancy',
    'total_consultancies',
    'percentage',
    'url'
]]

from IPython.display import HTML
pd.set_option('display.max_colwidth', -1)
HTML(links.to_html(escape=False))

