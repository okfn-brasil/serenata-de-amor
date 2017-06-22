
# coding: utf-8

# # Analysis to support article on cabs vs. apps
# 
# Simple notebook listing expenses with cabs and fuel to support [@vilapedro](https://github.com/vilapedro)'s article on cabs vs. apps.
# 
# First let's load the main dataset, using only the columns we need:

# In[1]:

import pandas as pd
import numpy as np

usecols = (
    'total_net_value',
    'congressperson_name',
    'subquota_number',
    'subquota_description',
    'cnpj_cpf',
    'year',
    'month'
)

dtype={
    'cnpj_cpf': np.str,
    'subquota_number': np.str
}

df = pd.read_csv(
    '../data/2017-03-15-reimbursements.xz',
    usecols=usecols, dtype=dtype
)


# As he's writing about expenses srating from June/2014, let's crop our data:

# In[2]:

year2014 = df[df.year == 2014]
year2014june = year2014[year2014['month'] >= 6]
reimbursements = year2014june.append(df[df['year'] >= 2015])
reimbursements.year.unique()


# And according to his analysis on cabs usage, we're only interested in 9 specific represenatives:

# In[3]:

names = (
    'Marcelo Squassoni',
    'Vanderlei Macris',
    'Francisco Floriano',
    'Marcus Vicente',
    'Marcelo Delaroli',
    'Renata Abreu',
    'Alessandro Molon',
    'Chico D’Angelo',
    'Zeca Dirceu'
)
names = tuple(name.upper() for name in names)
deputies = reimbursements[reimbursements.congressperson_name.isin(names)]
deputies.congressperson_name.unique()


# Now let's filter only the expenses done with fuel…

# In[4]:

fuel = deputies[deputies.subquota_number == '3']
fuel.subquota_description.unique()


# …and with cabs:

# In[5]:

taxi = deputies[deputies.subquota_number == '122']
taxi.subquota_description.unique()


# Finally let's group expenses month by month to compare — the hypothesis is that expenses with fuel should decrease when expenses with cabs incresase:

# In[6]:

def group_by_month(df):
    keys = ('congressperson_name', 'year', 'month')
    return df.groupby(keys)['total_net_value']         .agg([np.sum, len])         .rename(columns={'len': 'expenses'})


# In[7]:

grouped_fuel = group_by_month(fuel)
grouped_fuel


# In[8]:

grouped_taxi = group_by_month(taxi)
grouped_taxi


# And… let's export some Excel:

# In[9]:

# output = pd.ExcelWriter('fuel_vs_cabs.xlsx')
# grouped_fuel.to_excel(output,'Grouped Fuel')
# grouped_taxi.to_excel(output,'Grouped Taxi')
# fuel.to_excel(output,'Fuel')
# output.save()


# According to Pedro nothing interesting in this comparison, but let's leave this notebook here if anyone else is interested in this comparison.
