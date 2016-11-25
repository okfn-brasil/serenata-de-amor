
# coding: utf-8

# # Traveled speeds
# 
# The Quota for Exercise of Parliamentary Activity says that meal expenses can be reimbursed just for the politician, excluding guests and assistants. Creating a feature with information of traveled speed from last meal can help us detect anomalies compared to other expenses.
# 
# Since we don't have in structured data the time of the expense, we want to anylize the group of expenses made in the same day.
# 
# * Learn how to calculate distance between two coordinates.
# * Filter "Congressperson meal" expenses.
# * Order by date.
# * Merge `reimbursements.xz` dataset with `companies.xz`, so we have latitude/longitude for each expense.
# * Remove expenses with less than 12 hours of distance between each other.
# 
# ...
# 
# 
# * Filter specific congressperson.

# In[1]:

import pandas as pd
import numpy as np

reimbursements = pd.read_csv('../data/2016-11-19-reimbursements.xz',
                             dtype={'cnpj_cpf': np.str},
                             low_memory=False)


# In[2]:

reimbursements.iloc[0]


# In[3]:

reimbursements = reimbursements[reimbursements['subquota_description'] == 'Congressperson meal']
reimbursements.shape


# In[4]:

reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], errors='coerce')
reimbursements.sort_values('issue_date', inplace=True)


# In[5]:

companies = pd.read_csv('../data/2016-09-03-companies.xz', low_memory=False)
companies.shape


# In[6]:

companies.iloc[0]


# In[7]:

companies['cnpj'] = companies['cnpj'].str.replace(r'[\.\/\-]', '')


# In[8]:

dataset = pd.merge(reimbursements, companies, left_on='cnpj_cpf', right_on='cnpj')
dataset.shape


# In[9]:

dataset.iloc[0]


# Remove party leaderships from the dataset before calculating the ranking.

# In[10]:

dataset = dataset[dataset['congressperson_id'].notnull()]
dataset.shape


# And also remove companies mistakenly geolocated outside of Brazil.

# In[11]:

is_in_brazil = (dataset['longitude'] < -34.7916667) &     (dataset['latitude'] < 5.2722222) &     (dataset['latitude'] > -33.742222) &     (dataset['longitude'] > -73.992222)
dataset = dataset[is_in_brazil]
dataset.shape


# In[12]:

# keys = ['applicant_id', 'issue_date']
keys = ['congressperson_name', 'issue_date']
aggregation = dataset.groupby(keys)['total_net_value'].     agg({'sum': np.sum, 'expenses': len, 'mean': np.mean})


# In[13]:

aggregation['expenses'] = aggregation['expenses'].astype(np.int)


# In[14]:

aggregation.sort_values(['expenses', 'sum'], ascending=[False, False]).head(10)


# In[15]:

len(aggregation[aggregation['expenses'] > 7])


# In[16]:

keys = ['congressperson_name', 'issue_date']
cities = dataset.groupby(keys)['city'].     agg({'city': lambda x: len(set(x)), 'city_list': lambda x: ','.join(set(x))}).sort_values('city', ascending=False)


# In[17]:

cities.head()


# In[18]:

cities[cities['city'] >= 4].shape


# Would be helpful for our analysis to have a new column containing the traveled distance in this given day.

# In[19]:

from geopy.distance import vincenty as distance
from IPython.display import display

x = dataset.iloc[0]
display(x[['cnpj', 'city', 'state_y']])
distance(x[['latitude', 'longitude']],
         x[['latitude', 'longitude']])


# In[20]:

dataset.shape


# In[21]:

dataset[['latitude', 'longitude']].dropna().shape


# In[22]:

from itertools import tee

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def calculate_distances(x):
    coordinate_list = x[['latitude', 'longitude']].values
    distance_list = [distance(*coordinates_pair).km
                     for coordinates_pair in pairwise(coordinate_list)]
    return np.nansum(distance_list)

distances = dataset.groupby(keys).apply(calculate_distances)


# In[23]:

distances = distances.reset_index()     .rename(columns={0: 'distance_traveled'})     .sort_values('distance_traveled', ascending=False)
distances.head()


# Now we are not ordering the list of cities, just calculating the distance between them in the order they are in the dataset. Since we don't have the time of the expenses to know their real order, one approach is to consider the shortest path between in the cities visited in the day by the congressperson.

# In[24]:

import networkx as nx

G = nx.Graph()


# In[25]:

G=nx.path_graph(5)
G


# In[26]:

path=nx.all_pairs_shortest_path(G)
path


# In[27]:

path[0][4]


# In[28]:

random_congressperson_day = cities[cities['city'] == 3].sample(random_state=0).reset_index().iloc[0]
matching_keys = ['congressperson_name', 'issue_date']
matches =     (dataset['congressperson_name'] == random_congressperson_day['congressperson_name']) &     (dataset['issue_date'] == random_congressperson_day['issue_date'])
expenses_for_graph = dataset[matches]
expenses_for_graph


# In[29]:

def city_and_state(row):
    return '{} - {}'.format(row['city'], row['state_y'])

expenses_for_graph['city_state'] = expenses_for_graph.apply(city_and_state, axis=1)
expenses_for_graph['city_state']


# In[30]:

lat_longs = expenses_for_graph[['city_state', 'latitude', 'longitude']].values
# np.apply_along_axis(lambda x: (x[0], x[1]), axis=1, arr=lat_longs)


# * Create a node for each of the cities.
# * Connect each city with every other (making it a "complete graph").
# * Give weight to each of the edges, which should correspond to the distance between the cities.
# * Create a new node (artificial origin/destination for the Traveling Salesman).
# * Connect this new node with every other node, with weight equal to zero.
# * Run the Traveling Salesman algorithm starting from the artificial node.
# 
# <!-- * Run the Hamiltonian path algorithm. -->

# In[31]:

from itertools import combinations

list(combinations(lat_longs.tolist(), 2))


# In[32]:

def create_node(row):
    print(row[0], row[1], row[2])
    cities_graph.add_node(row[0], pos=(row[1], row[2]))
    return 42

cities_graph = nx.Graph()
np.apply_along_axis(create_node, axis=1, arr=lat_longs)

edges = list(combinations(lat_longs.tolist(), 2))
for edge in edges:
    weight = distance(edge[0][1:], edge[1][1:]).km
    print(edge[0][0], edge[1][0], weight)
    cities_graph.add_edge(edge[0][0], edge[1][0], weight=weight)


# In[33]:

# cities_graph.add_node('starting_point')
# new_edges = [('starting_point', node) for node in cities_graph.nodes()]
# cities_graph.add_edges_from(new_edges, weight=0)


# In[34]:

cities_graph.nodes()


# In[35]:

cities_graph.edges()


# 1. Acreditamos no Gist.
# 2. Revisamos o Gist.
# 3. Simplesmente esquecemos "distância mínima" e somamos todas as distâncias do complete graph.

# In[36]:

def hamilton(G):
    F = [(G,[G.nodes()[0]])]
    n = G.number_of_nodes()
    while F:
        graph,path = F.pop()
        confs = []
        for node in graph.neighbors(path[-1]):
            conf_p = path[:]
            conf_p.append(node)
            conf_g = nx.Graph(graph)
            conf_g.remove_node(path[-1])
            confs.append((conf_g,conf_p))
        for g,p in confs:
            if len(p)==n:
                return p
            else:
                F.append((g,p))
    return None

hamilton(cities_graph)


# In[37]:

# print(lat_longs)
edges = list(combinations(lat_longs.tolist(), 2))
np.sum([distance(edge[0][1:], edge[1][1:]).km for edge in edges])


# In[38]:

def calculate_sum_distances(x):
    coordinate_list = x[['latitude', 'longitude']].values
    edges = list(combinations(coordinate_list, 2))
    return np.sum([distance(edge[0][1:], edge[1][1:]).km for edge in edges])

distances = dataset.groupby(keys).apply(calculate_sum_distances)


# In[39]:

distances = distances.reset_index()     .rename(columns={0: 'distance_traveled'})     .sort_values('distance_traveled', ascending=False)
distances.head()


# In[40]:

dataset_with_distances =     pd.merge(aggregation.reset_index(),
             distances,
             left_on=keys,
             right_on=keys)
dataset_with_distances.sort_values(['distance_traveled', 'expenses'], ascending=[False, False]).head(10)


# In[41]:

from altair import Chart

Chart(dataset_with_distances).mark_point().encode(
    x='expenses',
    y='distance_traveled',
)


# In[42]:

dataset_with_distances.describe()


# In[43]:

dataset_with_distances[dataset_with_distances['expenses'] > 4].shape


# In[44]:

expenses_ceiling = dataset_with_distances['expenses'].mean() +     (3 * dataset_with_distances['expenses'].std())
expenses_ceiling


# In[45]:

distance_traveled_ceiling = dataset_with_distances['distance_traveled'].mean() +     (3 * dataset_with_distances['distance_traveled'].std())
distance_traveled_ceiling


# In[46]:

is_anomaly = (dataset_with_distances['expenses'] > expenses_ceiling) &     (dataset_with_distances['distance_traveled'] > distance_traveled_ceiling)
dataset_with_distances[is_anomaly].shape


# In[47]:

dataset_with_distances.loc[is_anomaly].sum()


# In[48]:

dataset_with_distances.loc[is_anomaly, 'mean'].mean()


# In[49]:

len(dataset_with_distances.loc[is_anomaly]) / len(dataset_with_distances)


# In[50]:

dataset_with_distances[is_anomaly]     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# # Outlier detection using x algorithm
# If we get similar results to this simple method, we expect to find the same congressperon, but not the same days. If we find the same days, our approach is not good enough compared to the simples method because we already that in the previous section we did not considered the combination of features but just their values compared to the distribuition of each feature (column).
# We expect the same congrespeople because the previous results shows that those person are travelling a lot more compared to the other congresspeople. For instance, Dr. Adilson Soares appears with 106 abnormal days more then twice than the second in the ranking, Sandra Rosado. Thus, would be expected to see him in the top ranking of congresspeople with abnormal meal expenses.

# ## Histogram of expenses

# In[51]:

get_ipython().magic('matplotlib inline')
import seaborn as sns
sns.set(color_codes=True)

sns.distplot(dataset_with_distances['expenses'],
             bins=14,
             kde=False)


# In[52]:

sns.distplot(dataset_with_distances.query('1 < expenses < 8')['expenses'],
    bins=6,
    kde=False
)


# ## Histogram of distance traveled

# In[53]:

query = '(1 < expenses < 8)'
sns.distplot(dataset_with_distances.query(query)['distance_traveled'],
             bins=20,
             kde=False)


# In[54]:

query = '(1 < expenses < 8) & (0 < distance_traveled < 5000)'
sns.distplot(dataset_with_distances.query(query)['distance_traveled'],
             bins=20,
             kde=False)


# In[55]:

from sklearn.ensemble import IsolationForest


# In[56]:

predictor_keys = ['mean', 'expenses', 'sum', 'distance_traveled']

model = IsolationForest()
model.fit(dataset_with_distances[predictor_keys])


# In[57]:

query = '(congressperson_name == "DR. ADILSON SOARES")'
expected_abnormal_day = dataset_with_distances[is_anomaly]     .query(query)     .sort_values('expenses', ascending=False).iloc[0]

expected_abnormal_day


# In[58]:

model.predict([expected_abnormal_day[predictor_keys]])


# In[59]:

y = model.predict(dataset_with_distances[predictor_keys])
len(y[y == -1])


# In[ ]:



