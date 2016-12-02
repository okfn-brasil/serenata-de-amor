
# coding: utf-8

# # Lodging Expense Analysis (an attempt to partially address issue #26)

# This analysis tries to find anomalies in lodging expenses by internal comparison.
# 
# It is worth noting that this code doesn't take some very important things into consideration:
# 
# * There seems to be no way to know the amount of days spent at the hotel
# * Also no special treatment to holidays and weekends is applied
# 
# Such things can cause false positives, so the results presented here must be taken with a grain of salt. To put it another way, this research should be used for further data analysis, they're not yet ready for manual investigation of any sort.

# In[1]:

import pandas as pd
import numpy as np


# In[2]:

data = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                  dtype={ 'cnpj_cpf': np.str, 'reimbursement_numbers': np.str })


# First thing we should do is to filter our dataset according to @Irio's suggestion.

# In[3]:

filtered_data = data[data['subquota_description'] == 'Lodging, except for congressperson from Distrito Federal']
filtered_data.head(2)


# Next, it is handy to further simplify our model. Lets focus only on the hotel's social ID (CNPJ) and the receipt's declared value.

# In[4]:

lodging_data = filtered_data[['cnpj_cpf', 'total_net_value']]
lodging_data.head()


# Now let's find out the average value and standard deviation for each supplier that has at least 10 receipts (so our results have a higher chance of being meaningful).

# In[5]:

per_supplier_data = lodging_data.groupby('cnpj_cpf').agg({ 'total_net_value': ['count', 'mean', 'std'] })
meaningful_supplier_data = per_supplier_data[per_supplier_data['total_net_value']['count'] >= 10]

# http://stackoverflow.com/questions/14507794/python-pandas-how-to-flatten-a-hierarchical-index-in-columns
meaningful_supplier_data.columns = [' '.join(col).strip() for col in meaningful_supplier_data.columns.values]

meaningful_supplier_data.head()


# With this data we can join back with our original dataset and find potentially suspicious receipts.

# In[6]:

joined_data = pd.merge(filtered_data, meaningful_supplier_data, left_on='cnpj_cpf', right_index=True)
suspicous_predicate = joined_data.total_net_value > (joined_data['total_net_value mean'] + (joined_data['total_net_value std'] * 2))
suspicious_data = joined_data[suspicous_predicate][['congressperson_name', 'cnpj_cpf', 'supplier', 'total_net_value', 'total_net_value mean', 'total_net_value std', 'total_net_value count']]
suspicious_data.head()


# Let's check the first result (DILCEU SPERAFICO's receipt for GELINSKI HOTEIS E TURISMO LTDA) to be sure we got our math correctly.

# In[27]:

filtered_data[filtered_data.cnpj_cpf == '77124980000169'][['document_id', 'supplier', 'total_net_value']]


# We can conclude that 5 hundred is indeed highly above average for this supplier (maybe not enough to really be suspicious? There is knobs available at `suspicious_predicate` that may be improved). Also note that we have different supplier names related to the same company social ID (CNPJ).
