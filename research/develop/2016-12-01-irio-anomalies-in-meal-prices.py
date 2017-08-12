
# coding: utf-8

# # Anomalies in meal prices
# 
# In the Chamber of Deputies' CEAP, there is a list of 1,000's of meal expenses made by congresspeople. The law says that the congressperson cannot pay for any other, even being her advisor or SO. We want to work on this analysis to find possibly illegal and immoral expenses. They may have happened when the politician spent more than needed (e.g. the whole menu costs X but the bill was 2X) or too much in an specific period of time. In the end, we also want to alert about too expensive reibursements, even with an explanation behind of it.
# 
# Note: remember to correct prices with an inflation index (e.g. IPCA).

# In[1]:

get_ipython().magic('matplotlib inline')
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(color_codes=True)

plt.rcParams['figure.figsize'] = (20, 10)


# In[2]:

from serenata_toolbox.datasets import fetch

fetch('2016-11-19-reimbursements.xz', '../data')
fetch('2016-09-03-companies.xz', '../data')
fetch('2016-11-29-yelp-companies.xz', '../data')
fetch('2016-12-02-foursquare-companies.xz', '../data')


# In[3]:

import numpy as np
import pandas as pd

dataset = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                      dtype={'applicant_id': np.str,
                             'cnpj_cpf': np.str,
                             'congressperson_id': np.str,
                             'subquota_number': np.str},
                      low_memory=False)
dataset = dataset[dataset['congressperson_id'].notnull()]
dataset['issue_date'] = pd.to_datetime(dataset['issue_date'], errors='coerce')
dataset['issue_date_day'] = dataset['issue_date'].apply(lambda date: date.day)
dataset['issue_date_month'] = dataset['issue_date'].apply(lambda date: date.month)
dataset['issue_date_year'] = dataset['issue_date'].apply(lambda date: date.year)
dataset['issue_date_weekday'] = dataset['issue_date'].apply(lambda date: date.weekday())
dataset['issue_date_week'] = dataset['issue_date'].apply(lambda date: date.week)


# The `companies.xz` dataset has businesses placed outside Brazilian area. We intentionally disconsider them.

# In[4]:

is_in_brazil = '(-73.992222 < longitude < -34.7916667) & (-33.742222 < latitude < 5.2722222)'
companies = pd.read_csv('../data/2016-09-03-companies.xz',
                        dtype={'cnpj': np.str},
                        low_memory=False)
companies = companies.query(is_in_brazil)
companies['cnpj'] = companies['cnpj'].str.replace(r'\D', '')
dataset = pd.merge(dataset, companies,
                   how='left',
                   left_on='cnpj_cpf',
                   right_on='cnpj',
                   suffixes=('', '_company'))


# In[5]:

dataset =     dataset.query('subquota_description == "Congressperson meal"')
companies =     companies[companies['cnpj'].isin(dataset.loc[dataset['cnpj'].notnull(),
                                                 'cnpj'])]


# In[6]:

dataset['total_net_value'].describe()


# In[7]:

dataset['total_net_value'].median()


# In[8]:

sns.distplot(dataset['total_net_value'],
             bins=30,
             kde=False)


# In[9]:

bottom_99 = dataset['total_net_value'].quantile(0.99)
bottom_99


# In[10]:

dataset[dataset['total_net_value'] < bottom_99].shape


# In[11]:

sns.distplot(dataset.loc[dataset['total_net_value'] < bottom_99, 'total_net_value'],
             bins=30,
             kde=False)


# In[12]:

bottom_99_dataset = dataset.query('total_net_value > {}'.format(bottom_99))
ranking = bottom_99_dataset.groupby('state_company')['total_net_value']     .median().sort_values(ascending=False)

sns.boxplot(x='state_company',
            y='total_net_value',
            data=bottom_99_dataset,
            order=ranking.index)


# In[13]:

bottom_99_dataset.query('state_company == "CE"').shape


# In[14]:

dataset.query('state_company == "CE"').shape


# In[15]:

bottom_99_dataset['state_company'].isnull().sum()


# In[16]:

bottom_99_dataset.query('state_company == "CE"')     .sort_values('total_net_value', ascending=False)


# ## Using Yelp to improve prices information

# In[17]:

yelp = pd.read_csv('../data/2016-11-29-yelp-companies.xz',
                   low_memory=False)
yelp.head()


# We have data for just 8.6% of the companies which received from the "Congressperson meal" subquota.

# In[18]:

yelp['price'].notnull().sum()


# In[19]:

companies.shape


# In[20]:

yelp['price'].isnull().sum()


# In[21]:

yelp['price.int'] = yelp['price'].str.len()
states_with_records =     yelp[yelp['price'].notnull()].groupby('location.state')['location.state'].count() > 10
states_with_records = states_with_records[states_with_records].index


# In[22]:

yelp_just_significant_states =     yelp[yelp['price'].notnull() &
         yelp['location.state'].isin(states_with_records)]
yelp_just_significant_states['location.state'].value_counts()


# Yelp won't be that useful for now, since we don't have a lot of data. Will leave it for another analysis.

# ## Predict prices

# The idea here is to try to predict the "right range for prices" in a specific place. If we can have a good accuracy, everything far from the prediction could be considered an outlier.

# In[23]:

bottom_99_dataset.iloc[0, :57]


# **DummyRegressor with mean strategy as a baseline**

# In[24]:

from sklearn.dummy import DummyRegressor
from sklearn.model_selection import train_test_split

X = bottom_99_dataset[['year']]
y = bottom_99_dataset['total_net_value']
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

model = DummyRegressor(strategy='mean')
model.fit(X_train, y_train)
model.score(X_test, y_test)


# In[25]:

from sklearn.preprocessing import LabelEncoder

le_state = LabelEncoder()
le_city = LabelEncoder()
factor_columns = ['state_company', 'city']
model_dataset = bottom_99_dataset.dropna(subset=factor_columns)
model_dataset['state_company'] = le_state.fit_transform(model_dataset['state_company'])
model_dataset['city'] = le_city.fit_transform(model_dataset['city'])

model_columns = ['cnpj',
                 'issue_date_day',
                 'issue_date_month',
                 'issue_date_year']
X = model_dataset[model_columns + factor_columns]
y = model_dataset['total_net_value']
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)


# **LinearRegression**
# 
# Not very good accuracy.

# In[26]:

from sklearn.linear_model import LinearRegression

model = LinearRegression(n_jobs=-1)
model.fit(X_train, y_train)
model.score(X_test, y_test)


# What if we could improve it using the type of business as a feature? e.g. restaurant, hotel, grill...

# In[27]:

import unicodedata

def normalize_string(string):
    if isinstance(string, str):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')


# In[28]:

import nltk
from sklearn.feature_extraction.text import CountVectorizer

stopwords = nltk.corpus.stopwords.words('portuguese')
count_vect = CountVectorizer(stop_words=stopwords)
trade_names = dataset.loc[dataset['supplier'].notnull(),
                          'supplier'].unique()
trade_names = np.vectorize(normalize_string)(trade_names)
dataset_counts = count_vect.fit_transform(trade_names)


# In[29]:

frequent_words = sorted(list(zip(count_vect.get_feature_names(),
    np.asarray(dataset_counts.sum(axis=0)).ravel())), key=lambda x: -x[1])


# In[30]:

frequent_words[:20]


# In[31]:

frequent_words = dict(frequent_words)

excluded_keywords = ['ltda', 'cia', 'epp']
[frequent_words.pop(keyword) for keyword in excluded_keywords]


# In[32]:

def business_type(name):
    fun = np.vectorize(lambda x: normalize_string(x))
    keywords = set(fun(name.split(' '))) - set(stopwords)
    key_freqs = list(map(lambda x: (x, frequent_words.get(x)), list(keywords)))
    key_freqs = [key_freq for key_freq in key_freqs if key_freq[1] is not None]
    if key_freqs:
        key_freq = max(key_freqs, key=lambda x: x[1])
        return key_freq[0]

dataset['supplier_keyword'] = dataset['supplier'].apply(business_type)
bottom_99_dataset['supplier_keyword'] =     bottom_99_dataset['supplier'].apply(business_type)


# In[33]:

le_state = LabelEncoder()
le_city = LabelEncoder()
le_supplier_keyword = LabelEncoder()
factor_columns = ['state_company', 'supplier_keyword']
model_dataset = bottom_99_dataset.dropna(subset=factor_columns)
model_dataset['state_company'] = le_state.fit_transform(model_dataset['state_company'])
model_dataset['city'] = le_city.fit_transform(model_dataset['city'])
model_dataset['supplier_keyword'] = le_city.fit_transform(model_dataset['supplier_keyword'])

model_columns = ['cnpj',
                 'issue_date_day',
                 'issue_date_month',
                 'issue_date_year']
X = model_dataset[model_columns + factor_columns]
y = model_dataset['total_net_value']
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)


# In[34]:

model = LinearRegression(n_jobs=-1)
model.fit(X_train, y_train)
model.score(X_test, y_test)


# Still not good enough. In fact, there's a serious mistake when considering this linear regression method for outlier detection: not just we're assuming that prices follow a linear regression (IMHO still good assumption, though), but outliers should be removed before running the regression. In other words, to find outliers, we must first remove them, having the regression score as just a accuracy estimator. May still be an interesting approach but we want to engage with something simpler first, to get the easier and most anomalous results.

# ## Common CNPJs
# 
# Expenses in the same restaurant are expected to follow a normal distribution. Can we find outliers in companies with enough expenses to analyze?

# In[35]:

from scipy.stats import normaltest

def normaltest_pvalue(values):
    if len(values) >= 20:
        return normaltest(values).pvalue
    else:
        return 1

net_values_by_cnpj = dataset.groupby('cnpj_cpf')['total_net_value']     .agg([len, np.mean, np.std, normaltest_pvalue])     .sort_values('len', ascending=False)     .reset_index()
net_values_by_cnpj['threshold'] = net_values_by_cnpj['mean'] +     3 * net_values_by_cnpj['std']
applicants_per_cnpj = dataset.groupby('cnpj_cpf')['applicant_id']     .aggregate(lambda x: len(set(x))).reset_index()     .rename(columns={'applicant_id': 'congresspeople'})
net_values_by_cnpj = pd.merge(net_values_by_cnpj, applicants_per_cnpj)
net_values_by_cnpj.head()


# In[36]:

len(net_values_by_cnpj.query('normaltest_pvalue < .05')) / len(net_values_by_cnpj)


# In[37]:

data_with_threshold = pd.merge(dataset, net_values_by_cnpj, on='cnpj_cpf')     .sort_values('total_net_value', ascending=False)


# In[38]:

data_with_threshold['main_activity'] =     data_with_threshold['main_activity'].apply(normalize_string)


# Let's discard hotel reibursements. There's no method yet to discover for how long the congressperson stayed in the hotel, so we can expect a high standard deviation in their expenses. Even when detecting outliers, it's too hard to investigate manually given the same reason.
# 
# Here, we just consider CNPJs where we have more than 20 reimbursements, from at least 3 congresspeople.

# In[39]:

is_hotel_reimbursement = data_with_threshold['main_activity']     .str.contains('hoteis').astype(np.bool)
outliers = data_with_threshold[~is_hotel_reimbursement]     .query('(congresspeople > 3) & (len >= 20) & (total_net_value > threshold)')
print(len(outliers), outliers['total_net_value'].sum())


# ## Foursquare
# 
# Before totally discarding it, let's see how significant is the Foursquare dataset.

# In[40]:

foursquare = pd.read_csv('../data/2016-12-02-foursquare-companies.xz',
                         low_memory=False)
foursquare.head()


# In[41]:

foursquare.iloc[0]


# In[42]:

print(foursquare['price.tier'].notnull().sum(),
      foursquare['price.tier'].notnull().sum() / len(companies),
      foursquare.query('confirmed_match == True')['price.tier'].notnull().sum() / len(companies))


# ### Clustering for find the best group for a new restaurant

# In[43]:

companies.shape


# In[44]:

# is_cnpj = (dataset['cnpj_cpf'].str.len() == 14) & \
#     dataset['cnpj_cpf'].notnull() & \
#     dataset['document_type'] != 2
# cnpjs = dataset.sort_values('issue_date') \
#     .loc[is_cnpj, ['cnpj_cpf', 'supplier']] \
#     .drop_duplicates('cnpj_cpf', keep='last')
# cnpjs.head()


# In[45]:

is_cnpj = dataset['cnpj_cpf'].str.len() == 14
cnpj_list = dataset.loc[is_cnpj].groupby('cnpj')['total_net_value']     .agg([np.mean, np.std]).reset_index()
cnpj_list.shape


# In[46]:

cnpj_list.head()


# In[47]:

cnpj_list = pd.merge(cnpj_list,
                     dataset[['cnpj_cpf', 'supplier']].drop_duplicates('cnpj_cpf'),
                     how='left',
                     left_on='cnpj', right_on='cnpj_cpf')
del cnpj_list['cnpj_cpf']
cnpj_list.head()


# In[48]:

counts = dataset.loc[is_cnpj].groupby('cnpj')['applicant_id']     .agg({'congresspeople': (lambda x: len(np.unique(x))),
          'len': (lambda x: len(x))
         }).reset_index()

cnpj_list = pd.merge(cnpj_list, counts)


# **Calculate threshold for companies using their own receipts**

# In[49]:

threshold_for_cnpjs = cnpj_list.groupby('cnpj')     .apply(lambda x: x['mean'].mean() + 3 * x['std'].mean()).reset_index()     .rename(columns={0: 'threshold'})
threshold_for_cnpjs

cnpj_list = pd.merge(cnpj_list, threshold_for_cnpjs)
cnpj_list.head()


# In[50]:

HOTEL_REGEX = r'hote[l(eis)(ls)]'
is_hotel_reimbursement = (cnpj_list['supplier'].str.lower().str.contains(HOTEL_REGEX))


# Mark companies as having or not significant data.

# In[51]:

rows = (~is_hotel_reimbursement) &     (cnpj_list['congresspeople'] > 3) &     (cnpj_list['len'] > 20)
cnpj_list['has_significant_data'] = False
cnpj_list.loc[rows, 'has_significant_data'] = True


# In[52]:

print(cnpj_list['has_significant_data'].sum(),
      cnpj_list['has_significant_data'].sum() / len(cnpj_list['has_significant_data']))


# In[53]:

sns.lmplot('mean', 'std',
           data=cnpj_list.query('has_significant_data'),
           scatter_kws={'marker': 'D', 's': 100},
           size=10)


# **Predict threshold classifying companies in clusters by their price ranges**

# In[54]:

X = cnpj_list.loc[cnpj_list['has_significant_data'],
                  ['mean', 'std']]


# In[55]:

from sklearn.cluster import KMeans

model = KMeans(n_clusters=3, random_state=0)
model.fit(X)


# In[56]:

cnpj_list.loc[cnpj_list['has_significant_data'], 'y'] = model.predict(X)


# In[57]:

cnpj_list.query('y.notnull()').head()


# In[58]:

rows = (~cnpj_list['has_significant_data']) &     cnpj_list['std'].notnull() &     (~is_hotel_reimbursement)
X = cnpj_list.loc[rows, ['mean', 'std']]
cnpj_list.loc[rows, 'y'] = model.predict(X)


# In[59]:

threshold_for_groups = cnpj_list.groupby('y')     .apply(lambda x: x['mean'].mean() + 4 * x['std'].mean()).reset_index()     .rename(columns={0: 'threshold'})
threshold_for_groups


# In[60]:

group_thresholds = pd.merge(cnpj_list.query('~has_significant_data'),
                            threshold_for_groups,
                            on='y',
                            suffixes=('', '_group'))

cnpj_list = pd.merge(cnpj_list,
                     group_thresholds[['cnpj', 'threshold_group']],
                     how='left')
cnpj_list.loc[~cnpj_list['has_significant_data'], 'threshold'] =     cnpj_list['threshold_group']


# In[61]:

cnpj_list.query('(~has_significant_data) & std.notnull()').head()


# In[62]:

cnpj_list.query('has_significant_data').head()


# In[63]:

cnpj_list.query('threshold.notnull()').sample(5, random_state=10)


# In[64]:

del cnpj_list['threshold_group']


# In[65]:

merged = pd.merge(dataset, cnpj_list,
                  how='left',
                  left_on='cnpj_cpf',
                  right_on='cnpj',
                  suffixes=('', '_company'))


# In[66]:

merged['supplier'] = merged['supplier'].astype(np.str)
is_hotel_reimbursement =     (merged['supplier'].str.lower().str.contains(HOTEL_REGEX))

merged[~is_hotel_reimbursement].query('total_net_value > threshold').shape


# In[67]:

keys = ['year',
        'congressperson_name',
        'document_id',
        'total_net_value',
        'threshold',
        'cnpj_cpf',
        'has_significant_data',
        'name']

merged['diff'] = merged['threshold'] - merged['total_net_value']
merged[~(is_hotel_reimbursement | merged['has_significant_data'])]     .query('(total_net_value > threshold)')     .sort_values('diff', ascending=False).head(10)[keys]


# In[68]:

merged[~is_hotel_reimbursement].shape


# In[69]:

merged[~is_hotel_reimbursement]     .query('(total_net_value > threshold)')['total_net_value'].shape


# In[70]:

merged[~is_hotel_reimbursement]     .query('(total_net_value > threshold)')['total_net_value'].sum()


# In[71]:

merged[~is_hotel_reimbursement]     .query('(total_net_value > threshold) & (has_significant_data == False)')['total_net_value'].shape


# ## Conclusions
# 
# For companies with significant data (defined by us as a company which received money at least 20x, from at least 3 distinct congresspeople), we use mean + 3 * std to detect outliers. Does not return all the suspect cases, but all of them, after some sampling investigation, seem to be very suspect.
# 
# Since there's "significant data" just for 4% of the companies, we need a way for extrapolating the results for not so known ones. For doing so, we classify companies in 3 clusters using K-Means, considering mean and standard deviation of their prices as features. Once classified, we consider their threshold mean + 4 * stds of their clusters (one extra std compared to places where we have enough reimbursements to know better).
# 
# Reimbursements made for expenses in hotels are discarded from this classifier, since they usually contain much more than meals (and we don't know for how long the congressperson was hosted in the place, not yet trustable for legal reports).

# In[ ]:



