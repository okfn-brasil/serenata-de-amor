
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# In[2]:

dataset = pd.read_csv('../data/2016-11-22-reimbursements.xz',
                      dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str},
                      low_memory=False)


# In[3]:

dataset = dataset[dataset['year']==2016]


# In[4]:

dataset.head()


# # Find spends: congress person per month

# In[5]:

def find_spends_by_month(df, applicant_id):
    '''
    Return a dataframe with the sum of values of spends by month
    of the congress person of "applicant_id"
    Parameters:
        - df: pandas dataframe to be sliced
        - applicant_id: unique id of the congress person
        
    Ex: find_spends_by_month(df, 731)
    Result dataframe contains:
        - 1/Jan sum
        - 2/Feb sum
        - 3/Mar sum
        - 4/Apr sum
        - 5/May sum
        - 6/Jun sum
        - 7/Jul sum
        - 8/Aug sum
        - 9/Sep sum
        - 10/Oct sum
        - 11/Nov sum
        - 12/Dec sum
        - name
    '''
    months={1:"Jan",
            2:"Feb",
            3:"Mar",
            4:"Apr",
            5:"May",
            6:"Jun",
            7:"Jul",
            8:"Aug",
            9:"Sep",
            10:"Oct",
            11:"Nov",
            12:"Dec"}
    df_applicant = df[df.applicant_id == applicant_id]
    result = {
        "name":df_applicant["congressperson_name"].unique()
    }
       
    for m in months.keys():
        data = df_applicant[df.month == m]
        result["{:>02}".format(m) + "/" + months[m]] = data.total_net_value.sum()
    
    df_final = pd.DataFrame([result])
     
    ax = df_final.plot(kind='bar', title ="Congress Person Spends by Month", figsize=(25, 20), legend=True, fontsize=12)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    plt.show()
    
    return pd.DataFrame([result])

find_spends_by_month(dataset, 731)


# # Find spends: Congress Person per Subquotas

# In[6]:

def find_spends_by_subquota(df, applicant_id):
    '''
    Return a dataframe with the sum of values of spends by subquotas
    of the congress person of "applicant_id"
    Parameters:
        - df: pandas dataframe to be sliced
        - applicant_id: unique id of the congress person
    '''
    df_applicant = df[df.applicant_id == applicant_id]
    result = {
        "name":df_applicant["congressperson_name"].unique()
    }
    
    for c in df["subquota_description"].unique():
        data = df_applicant[df.subquota_description == c]
        result[c] = data.total_net_value.sum()
    
    df_final = pd.DataFrame([result])
    ax = df_final.plot(kind='bar', title ="Congress Person Spends by Subquotas", figsize=(25, 20), legend=True, fontsize=12)
    ax.set_xlabel("Subquotas", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    plt.show()
    return pd.DataFrame([result])

find_spends_by_subquota(dataset, 731)


# In[7]:

def find_spends_by_subquota(df, applicant_id, month=None):
   '''
   Return a dataframe with the sum of values of spends by subquotas
   of the congress person of "applicant_id" and month "month"
   Parameters:
       - df: pandas dataframe to be sliced
       - applicant_id: unique id of the congress person
   '''
   df_applicant = df[df.applicant_id == applicant_id]
   
   result = {
       "name":df_applicant["congressperson_name"].unique(),
       "total": 0
       
   }
   if month != None:
       df_applicant = df_applicant[df_applicant.month==month]


   for c in df["subquota_description"].unique():
       data = df_applicant[df.subquota_description == c]
       result[c] = data.total_net_value.sum()
       result["total"] += result[c]
   
   df_final = pd.DataFrame([result])
   ax = df_final.plot(kind='bar', title ="Congress Person", figsize=(25, 20), legend=True, fontsize=12)
   ax.set_xlabel("Name", fontsize=12)
   ax.set_ylabel("Value", fontsize=12)
   plt.show()
   return pd.DataFrame([result])

find_spends_by_subquota(dataset, 731, 3)


# # Find spends: all congress people 

# In[8]:

def find_sum_of_values(df, aggregator, property):
    '''
    Return a dataframe with the statistics of values from "property"
    aggregated by unique values from the column "aggregator"
    Parameters:
        - df: pandas dataframe to be sliced
        - aggregator: dataframe column that will be
                      filtered by unique values
        - property: dataframe column containing values to be summed
    Ex: find_sum_of_values(data, 'congressperson_name', 'net_value')
    Result dataframe contains (for each aggregator unit):
        - property sum
        - property mean value
        - property max value
        - property mean value
        - number of occurences in total
    '''

    total_label = '{}_total'.format(property)
    max_label = '{}_max'.format(property)
    mean_label = '{}_mean'.format(property)
    min_label = '{}_min'.format(property)

    result = {
        'occurences': [],
        aggregator: df[aggregator].unique(),
        max_label: [],
        mean_label: [],
        min_label: [],
        total_label: [],

    }

    for item in result[aggregator]:
        if isinstance(df[aggregator].iloc[0], str):
            item = str(item)
        values = df[df[aggregator] == item]
        property_total = int(values[property].sum())
        occurences = int(values[property].count())

        result[total_label].append(property_total)
        result['occurences'].append(occurences)
        result[mean_label].append(property_total/occurences)
        result[max_label].append(np.max(values[property]))
        result[min_label].append(np.min(values[property]))

    return pd.DataFrame(result).sort_values(by=aggregator)

df = find_sum_of_values(dataset, "congressperson_name", "total_net_value")
df[:10]


# # Finding congress people that spent more than 500 thousand per year

# In[9]:

df = df[df.total_net_value_total > 500000]
df


# In[10]:

ax = df[["total_net_value_total"]].plot(kind='bar', title ="Congress Person Spends", figsize=(15, 10), legend=True, fontsize=12)
ax.set_xlabel("Congress Person", fontsize=12)
ax.set_ylabel("Value", fontsize=12)
plt.show()

