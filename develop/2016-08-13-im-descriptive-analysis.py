
# coding: utf-8

# In[1]:

get_ipython().magic('matplotlib inline')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[2]:

data = pd.read_csv('../data/2016-08-08-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# There are 374,484 expenses reimbursed in the past year.

# In[3]:

print(data.shape)


# In[4]:

data.head()


# In[5]:

data.iloc[0]


# In[6]:

def change_type_to_category(column):
    data[column] = data[column].astype('category')

category_columns = ['congressperson_id',
       'state', 'party', 'term_id',
       'subquota_number', 'subquota_group_id',
       'document_type', 'applicant_id']

[change_type_to_category(column) for column in category_columns]; None


# Data seems to contain outliers - negative net values and other records in the range of hundreds of thousands of Reais.

# In[7]:

sns.distplot(data['net_value'])


# In[8]:

data['net_value'].describe()


# Most expensive document reimbursed by the government: R$189,600.00

# In[9]:

data[data['net_value'] == data['net_value'].max()]


# There are negative net_values.

# In[10]:

sns.distplot(data.loc[data['net_value'] < 0, 'net_value'])


# Let's try to remove outliers.

# In[11]:

dist_range = data['net_value'].mean() + data['net_value'].std() * 3 * np.r_[-1, 1]
dist_range


# In[12]:

wo_outliers =     (data['net_value'] >= dist_range[0]) & (data['net_value'] <= dist_range[1])
data_wo_outliers = data[wo_outliers]
sns.distplot(data_wo_outliers['net_value'])


# 45% of the dataset have net values larger than 3 standard deviations from the mean. Meaning: tail does not contain just a few outliers, but a good portion of the dataset. Let's study what's in this long tail (greater than 3 stds).

# In[13]:

outliers = data[~data.isin(data_wo_outliers)['document_id']]
print(len(outliers), len(outliers) / len(data))


# In[14]:

outliers.head()


# In[15]:

outliers['subquota_description'].describe()


# In[16]:

from functools import partial

s_na_mean = partial(pd.Series.mean, skipna = True)
subquota_number_ranking =     outliers.groupby('subquota_number', as_index=False).agg({'net_value': np.nansum})

ranking_long_tail =     pd.merge(subquota_number_ranking,
             data[['subquota_number', 'subquota_description']].drop_duplicates('subquota_number', keep='first'),
             how='left',
             on='subquota_number').sort_values('net_value', ascending=False)


# In[17]:

ranking_long_tail.head()


# In[18]:

sns.barplot(x='subquota_description',
                    y='net_value',
                    data=ranking_long_tail)
locs, labels = plt.xticks()
plt.setp(labels, rotation=90); None


# Let's try to match a document found at http://www.camara.gov.br/cota-parlamentar/index.jsp. Can we generate URLs for the documents received for review?

# In[19]:

records =     (data['applicant_id'] == 3016) &     (data['month'] == 4) &     (data['subquota_number'] == 3)
data[records].iloc[0]


# In[20]:

def document_url(record):
    return 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/%s/%s/%s.pdf' %         (record['applicant_id'], record['year'], record['document_id'])

record = data[data['document_number'] == '632604'].iloc[0]
record


# From the document PDF, we could extract new features such as names of the products/services purchased, name of the seller, address of the business among other things.

# In[21]:

print(document_url(record))


# How about a random record? Is its `document_url` valid? YES!

# In[22]:

record = data.sample(random_state=0).iloc[0]
print(document_url(record))
record


# Who are these people? There were 803 different applicants last year.

# In[23]:

len(data['applicant_id'].unique())


# In[24]:

applicants_by_net_value =     pd.DataFrame(data.groupby(['applicant_id'], as_index=False).sum()[['applicant_id', 'net_value']])
applicants_by_net_value.head()


# In[25]:

len(applicants_by_net_value)


# In[26]:

congressperson_list = data[
    ['applicant_id', 'congressperson_name', 'party', 'state']]
congressperson_list = congressperson_list.drop_duplicates('applicant_id', keep='first')


# In[27]:

ranking = pd.merge(applicants_by_net_value,
                   congressperson_list,
                   how='left',
                   on='applicant_id').sort_values('net_value', ascending=False)
ranking.head(10)


# In[28]:

ranking['net_value'].describe()


# In[29]:

graph = sns.barplot(x='congressperson_name',
                    y='net_value',
                    data=ranking)
graph.axes.get_xaxis().set_ticks([]); None


# In[30]:

def x_label_generator(record):
    return '(%s) %s - %s' % (record['party'], record['congressperson_name'], record['state'])

ranking['x_label'] = ranking.apply(x_label_generator, axis=1)


# Apparently, politicians from states further away from Distrito Federal expent more. We could perform an analysis on distance to the capital and the home state from the politician.

# In[31]:

sns.barplot(x='x_label',
            y='net_value',
            data=ranking.head(30))
locs, labels = plt.xticks()
plt.setp(labels, rotation=90); None


# In[32]:

# empty cpf/cnpj for foreign expenses

