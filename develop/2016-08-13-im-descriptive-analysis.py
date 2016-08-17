
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
       'document_type', 'applicant_id', 'congressperson_name']

[change_type_to_category(column) for column in category_columns]; None


# Last year, R$213,668,049.56 were spent without public bidding. On average, each of the 374,484 expenses had a value of 570 Reais.

# In[7]:

data['net_value'].describe()


# In[8]:

data['net_value'].sum()


# Data seems to contain outliers. Negative net values and other records in the range of hundreds of thousands of Reais.

# In[9]:

sns.distplot(data['net_value'])


# Most expensive document reimbursed by the government: R$189,600.00

# In[10]:

most_expensive_reimbursement =     data[data['net_value'] == data['net_value'].max()].iloc[0]
most_expensive_reimbursement


# ## Negative net values

# Talking about negative values...

# In[11]:

negative_net_values = data[data['net_value'] < 0]
print(len(negative_net_values), len(negative_net_values) / len(data))


# In[12]:

sns.distplot(negative_net_values['net_value'])


# Not really sure what they mean.

# In[13]:

negative_net_values.sample(random_state=0).iloc[0]


# ## Long (right) tail

# Let's try to remove outliers.

# In[14]:

dist_range = data['net_value'].mean() + data['net_value'].std() * 3 * np.r_[-1, 1]
wo_outliers =     (data['net_value'] >= dist_range[0]) & (data['net_value'] <= dist_range[1])
data_wo_outliers = data[wo_outliers]
sns.distplot(data_wo_outliers['net_value'])


# ### Top 45%

# 45% of the dataset have net values larger than 3 standard deviations from the mean. Meaning: tail does not contain just a few outliers, but a good portion of the dataset. Let's study what is contained in this long tail (greater than 3 stds).

# In[15]:

outliers = data[~data.isin(data_wo_outliers)['document_id']]
print(len(outliers), len(outliers) / len(data))


# In[16]:

outliers.head()


# In[17]:

outliers['subquota_description'].describe()


# Let's build a ranking of expenses with higher values.

# In[18]:

from functools import partial

subquota_number_ranking = outliers.     groupby('subquota_number', as_index=False).     agg({'net_value': np.nansum})
subquotas = data[['subquota_number', 'subquota_description']].     drop_duplicates('subquota_number', keep='first')
subquota_number_ranking =     pd.merge(subquota_number_ranking,
             subquotas,
             how='left',
             on='subquota_number'). \
    sort_values('net_value', ascending=False)


# In[19]:

subquota_number_ranking.head()


# In[20]:

sns.barplot(x='subquota_description',
            y='net_value',
            data=subquota_number_ranking.head())
locs, labels = plt.xticks()
plt.setp(labels, rotation=90); None


# ### Top 1%

# How the top 1% look like?

# In[21]:

top_1_percent_num = int(.01 * len(data))
top_1_percent = data.     sort_values('net_value', ascending=False).     iloc[0:top_1_percent_num + 1]

top_1_percent_subquota_ranking = top_1_percent.     groupby('subquota_number', as_index=False).     agg({'net_value': np.nansum})
top_1_percent_subquota_ranking =     pd.merge(top_1_percent_subquota_ranking,
             subquotas,
             how='left',
             on='subquota_number'). \
    sort_values('net_value', ascending=False)


# In[22]:

top_1_percent_subquota_ranking.head()


# In[23]:

sns.barplot(x='subquota_description',
            y='net_value',
            data=top_1_percent_subquota_ranking.head())
locs, labels = plt.xticks()
plt.setp(labels, rotation=90); None


# This is the most expensive reimbursement from last year: R$189,600 for printing 120,000 units of something about the Elderly Statute.

# In[24]:

most_expensive_reimbursement


# Found at camara.gov.br, the URL of this expense receipt, in PDF: http://www.camara.gov.br/cota-parlamentar/documentos/publ/292/2015/5884288.pdf

# ## Description of each expense

# Let's try to match a document (PDF file) found at http://www.camara.gov.br/cota-parlamentar/index.jsp with this dataset. Can we generate URLs for the documents received for review?
# 
# Taking the following PDF as an example: http://www.camara.gov.br/cota-parlamentar/documentos/publ/3016/2015/5651163.pdf

# In[25]:

records =     (data['applicant_id'] == 3016) &     (data['month'] == 4) &     (data['subquota_number'] == 3)
data[records].iloc[0]


# It works!
# 
# From the document PDF, we could extract new features such as names of the products/services purchased, name of the seller, address of the business among other things.

# In[26]:

def document_url(record):
    return 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/%s/%s/%s.pdf' %         (record['applicant_id'], record['year'], record['document_id'])

record = data[data['document_number'] == '632604'].iloc[0]
record


# In[27]:

print(document_url(record))


# How about a random record? Is its `document_url` valid? YES!

# In[28]:

record = data.sample(random_state=0).iloc[0]
print(document_url(record))
record


# ## Who are these applicants?

# There were 803 different people receiving reimbursements last year.

# In[29]:

len(data['applicant_id'].unique())


# In[30]:

len(data['congressperson_name'].cat.categories)


# In[31]:

applicants_by_net_value =     pd.DataFrame(data.groupby(['applicant_id'], as_index=False).sum()[['applicant_id', 'net_value']])
applicants_by_net_value.head()


# In[32]:

congressperson_list = data[
    ['applicant_id', 'congressperson_name', 'party', 'state']]
congressperson_list = congressperson_list.     drop_duplicates('applicant_id', keep='first')
ranking = pd.merge(applicants_by_net_value,
                   congressperson_list,
                   how='left',
                   on='applicant_id').sort_values('net_value', ascending=False)
ranking.head(10)


# In[33]:

ranking['net_value'].describe()


# In[34]:

graph = sns.barplot(x='congressperson_name',
                    y='net_value',
                    data=ranking)
graph.axes.get_xaxis().set_ticks([]); None


# In[35]:

def x_label_generator(record):
    return '%s (%s - %s)' % (record['congressperson_name'],
                             record['party'],
                             record['state'])

ranking['x_label'] = ranking.apply(x_label_generator, axis=1)


# Apparently, politicians from states further away from Distrito Federal expent more. We could perform an analysis on distance to the capital and the home state from the politician.

# In[36]:

sns.barplot(x='x_label',
            y='net_value',
            data=ranking.head(30))
locs, labels = plt.xticks()
plt.setp(labels, rotation=90); None


# In[37]:

list(congressperson_list['congressperson_name'].cat.categories)


# A few `congressperson_name`s I can't properly explain yet:

# In[38]:

sdd = data[data['congressperson_name'] == 'SDD'].sample(random_state=0).iloc[0]
print(document_url(sdd))


# 721 expenses reimbursed to parties.

# In[39]:

parties = congressperson_list[congressperson_list['party'].isnull()]
parties


# In[40]:

party_expenses = data[data['applicant_id'].isin(parties['applicant_id'])]
len(party_expenses)


# In[41]:

party_expenses.head()


# ## Expenses abroad

# Are the expenses made outside of Brazil easily identifiable?

# In[42]:

wo_cnpj_cpf = data[data['cnpj_cpf'].isnull()]
len(wo_cnpj_cpf)


# In[43]:

wo_cnpj_cpf.head()


# In[44]:

wo_cnpj_cpf.sample(random_state=10).iloc[0]


# We could match politicians' location (from oficial agenda and social networks GPS info) with their expenses in a future analysis.

# In[45]:

wo_cnpj_cpf['supplier'].unique()


# Let's see how one that we know for sure being from another country, try to find specificities. Aparently, nothing special about it.

# In[46]:

montevideo_expense = wo_cnpj_cpf[wo_cnpj_cpf['supplier'] == 'Dazzler Hotel Montevideo'].iloc[0]
montevideo_expense


# In[47]:

print(document_url(montevideo_expense))


# In[48]:

wo_cnpj_cpf['supplier'] = wo_cnpj_cpf['supplier'].str.lower()
ranking_suppliers_wo_cnpj = wo_cnpj_cpf.     groupby('supplier', as_index=False).     count()[['supplier', 'applicant_id']].     sort_values('applicant_id', ascending=False)
ranking_suppliers_wo_cnpj.head()


# In[49]:

expenses_in_brazil = ranking_suppliers_wo_cnpj['supplier'].str.contains('correios') |     ranking_suppliers_wo_cnpj['supplier'].isin([
            'celular funcional',
            'imóvel funcional',
            'ramal'])
ranking_suppliers_wo_cnpj[~expenses_in_brazil]


# In[50]:

expense = data[data['supplier'].str.lower() == 'gordon ramsay\'s'].iloc[0]
expense


# In[51]:

print(document_url(expense))


# In[ ]:



