
# coding: utf-8

# # Traveled speeds between meals
# 
# The Quota for Exercise of Parliamentary Activity says that meal expenses can be reimbursed just for the politician, excluding guests and assistants. Creating a feature with information of "traveled speed" (i.e. too many meals in distant cities, in a short period of time) from last meal can help us detect anomalies compared to other expenses.
# 
# Since we don't have in structured data the time of the expense, we want to anylize the group of expenses made in the same day.

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

is_in_brazil = '(-73.992222 < longitude < -34.7916667) & (-33.742222 < latitude < 5.2722222)'
dataset = dataset.query(is_in_brazil)
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
cities = dataset.groupby(keys)['city'].     agg({'city': lambda x: len(set(x)),
         'city_list': lambda x: ','.join(set(x))}
       ).sort_values('city', ascending=False)


# In[17]:

cities.head()


# In[18]:

cities[cities['city'] >= 4].shape


# Would be helpful for our analysis to have a new column containing the traveled distance in this given day.

# ## New traveled distance column for each day/congressperson

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


# This way works, but the order of the visited cities is important. We need to find a way of calculate in the proper order or be fair in all calculations.

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

# Boworred from https://gist.github.com/mikkelam/ab7966e7ab1c441f947b
# Should we believe this algorithm is well implemented?
# Now is not the best way to learn how to do it ourselves...

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


# Calculating the minimum distance traveled each day is not so necessary, since we just need a number to say how far the visited cities are from each other. Summing the distances between all of their combinations is good enough.

# In[37]:

def calculate_sum_distances(x):
    coordinate_list = x[['latitude', 'longitude']].values
    edges = list(combinations(coordinate_list, 2))
    return np.sum([distance(edge[0][1:], edge[1][1:]).km for edge in edges])

distances = dataset.groupby(keys).apply(calculate_sum_distances)


# In[38]:

distances = distances.reset_index()     .rename(columns={0: 'distance_traveled'})     .sort_values('distance_traveled', ascending=False)
distances.head()


# In[39]:

cities.reset_index()


# In[40]:

aggregation = pd.merge(aggregation.reset_index(), cities.reset_index())


# In[41]:

dataset_with_distances =     pd.merge(aggregation,
             distances,
             left_on=keys,
             right_on=keys)
dataset_with_distances.sort_values(['distance_traveled', 'expenses'], ascending=[False, False]).head(10)


# In[42]:

get_ipython().magic('matplotlib inline')
import seaborn as sns

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances,
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10,
           order=2)


# In[43]:

dataset_with_distances.describe()


# In[44]:

dataset_with_distances[dataset_with_distances['expenses'] > 4].shape


# In[45]:

expenses_ceiling = dataset_with_distances['expenses'].mean() +     (3 * dataset_with_distances['expenses'].std())
expenses_ceiling


# In[46]:

distance_traveled_ceiling = dataset_with_distances['distance_traveled'].mean() +     (3 * dataset_with_distances['distance_traveled'].std())
distance_traveled_ceiling


# In[47]:

is_anomaly = (dataset_with_distances['expenses'] > expenses_ceiling) &     (dataset_with_distances['distance_traveled'] > distance_traveled_ceiling)
dataset_with_distances[is_anomaly].shape


# In[48]:

dataset_with_distances.loc[is_anomaly].sum()


# In[49]:

dataset_with_distances.loc[is_anomaly, 'mean'].mean()


# In[50]:

len(dataset_with_distances.loc[is_anomaly]) / len(dataset_with_distances)


# In[51]:

dataset_with_distances[is_anomaly]     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# In[52]:

dataset_with_distances['3_stds_anomaly'] = is_anomaly


# In[53]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances,
           fit_reg=False,
           hue='3_stds_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# In[54]:

expenses_ceiling = dataset_with_distances['expenses'].mean() +     (5 * dataset_with_distances['expenses'].std())
distance_traveled_ceiling = dataset_with_distances['distance_traveled'].mean() +     (5 * dataset_with_distances['distance_traveled'].std())
is_anomaly = (dataset_with_distances['expenses'] > expenses_ceiling) &     (dataset_with_distances['distance_traveled'] > distance_traveled_ceiling)
dataset_with_distances[is_anomaly].shape


# In[55]:

expenses_ceiling, distance_traveled_ceiling


# In[56]:

dataset_with_distances['5_stds_anomaly'] = is_anomaly


# In[57]:

len(dataset_with_distances.loc[is_anomaly]) / len(dataset_with_distances)


# In[58]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances,
           fit_reg=False,
           hue='5_stds_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# In[59]:

dataset_with_distances[is_anomaly]     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# # Outlier detection using IsolationForest algorithm
# 
# If we get similar results to this simple method, we expect to find the same congressperon, but not the same days. If we find the same days, our approach is not good enough compared to the simples method because we already that in the previous section we did not considered the combination of features but just their values compared to the distribuition of each feature (column).
# We expect the same congrespeople because the previous results shows that those person are travelling a lot more compared to the other congresspeople. For instance, Dr. Adilson Soares appears with 106 abnormal days more then twice than the second in the ranking, Sandra Rosado. Thus, would be expected to see him in the top ranking of congresspeople with abnormal meal expenses.

# ## Histogram of expenses

# In[60]:

get_ipython().magic('matplotlib inline')
import seaborn as sns
sns.set(color_codes=True)

sns.distplot(dataset_with_distances['expenses'],
             bins=14,
             kde=False)


# In[61]:

sns.distplot(dataset_with_distances.query('1 < expenses < 8')['expenses'],
    bins=6,
    kde=False
)


# ## Histogram of distance traveled

# In[62]:

query = '(1 < expenses < 8)'
sns.distplot(dataset_with_distances.query(query)['distance_traveled'],
             bins=20,
             kde=False)


# In[63]:

query = '(1 < expenses < 8) & (0 < distance_traveled < 5000)'
sns.distplot(dataset_with_distances.query(query)['distance_traveled'],
             bins=20,
             kde=False)


# In[64]:

from sklearn.ensemble import IsolationForest


# In[65]:

predictor_keys = ['mean', 'expenses', 'sum', 'distance_traveled']

model = IsolationForest(random_state=0)
model.fit(dataset_with_distances[predictor_keys])


# In[66]:

query = '(congressperson_name == "DR. ADILSON SOARES")'
expected_abnormal_day = dataset_with_distances[is_anomaly]     .query(query)     .sort_values('expenses', ascending=False).iloc[0]

expected_abnormal_day


# In[67]:

model.predict([expected_abnormal_day[predictor_keys]])


# In[68]:

y = model.predict(dataset_with_distances[predictor_keys])
dataset_with_distances['isolation_forest_anomaly'] = y == -1
dataset_with_distances['isolation_forest_anomaly'].sum()


# Too many anomalies found.

# In[69]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances,
           fit_reg=False,
           hue='isolation_forest_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# How about changing the predictor keys for something more prone to trigger illegal expenses (# of expenses and distance between cities of expenses each day)?

# In[70]:

predictor_keys = ['expenses', 'distance_traveled']

model = IsolationForest(contamination=.001, random_state=0)
model.fit(dataset_with_distances[predictor_keys])
model.predict([expected_abnormal_day[predictor_keys]])


# In[71]:

y = model.predict(dataset_with_distances[predictor_keys])
dataset_with_distances['isolation_forest_anomaly'] = y == -1
dataset_with_distances['isolation_forest_anomaly'].sum()


# In[72]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances,
           fit_reg=False,
           hue='isolation_forest_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# In[73]:

dataset_with_distances.query('isolation_forest_anomaly')     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# ## Local Outlier Factor

# In[74]:

# Authors: Nicolas Goix <nicolas.goix@telecom-paristech.fr>
#          Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
# License: BSD 3 clause

import numpy as np
from warnings import warn
from scipy.stats import scoreatpercentile

from sklearn.neighbors.base import NeighborsBase
from sklearn.neighbors.base import KNeighborsMixin
from sklearn.neighbors.base import UnsupervisedMixin

from sklearn.utils.validation import check_is_fitted
from sklearn.utils import check_array

__all__ = ["LocalOutlierFactor"]


class LocalOutlierFactor(NeighborsBase, KNeighborsMixin, UnsupervisedMixin):
    """Unsupervised Outlier Detection using Local Outlier Factor (LOF)

    The anomaly score of each sample is called Local Outlier Factor.
    It measures the local deviation of density of a given sample with
    respect to its neighbors.
    It is local in that the anomaly score depends on how isolated the object
    is with respect to the surrounding neighborhood.
    More precisely, locality is given by k-nearest neighbors, whose distance
    is used to estimate the local density.
    By comparing the local density of a sample to the local densities of
    its neighbors, one can identify samples that have a substantially lower
    density than their neighbors. These are considered outliers.

    Parameters
    ----------
    n_neighbors : int, optional (default=20)
        Number of neighbors to use by default for :meth:`kneighbors` queries.
        If n_neighbors is larger than the number of samples provided,
        all samples will be used.

    algorithm : {'auto', 'ball_tree', 'kd_tree', 'brute'}, optional
        Algorithm used to compute the nearest neighbors:

        - 'ball_tree' will use :class:`BallTree`
        - 'kd_tree' will use :class:`KDTree`
        - 'brute' will use a brute-force search.
        - 'auto' will attempt to decide the most appropriate algorithm
          based on the values passed to :meth:`fit` method.

        Note: fitting on sparse input will override the setting of
        this parameter, using brute force.

    leaf_size : int, optional (default=30)
        Leaf size passed to :class:`BallTree` or :class:`KDTree`. This can
        affect the speed of the construction and query, as well as the memory
        required to store the tree. The optimal value depends on the
        nature of the problem.

    p : integer, optional (default=2)
        Parameter for the Minkowski metric from
        :ref:`sklearn.metrics.pairwise.pairwise_distances`. When p = 1, this is
        equivalent to using manhattan_distance (l1), and euclidean_distance
        (l2) for p = 2. For arbitrary p, minkowski_distance (l_p) is used.

    metric : string or callable, default 'minkowski'
        metric used for the distance computation. Any metric from scikit-learn
        or scipy.spatial.distance can be used.

        If 'precomputed', the training input X is expected to be a distance
        matrix.

        If metric is a callable function, it is called on each
        pair of instances (rows) and the resulting value recorded. The callable
        should take two arrays as input and return one value indicating the
        distance between them. This works for Scipy's metrics, but is less
        efficient than passing the metric name as a string.

        Valid values for metric are:

        - from scikit-learn: ['cityblock', 'cosine', 'euclidean', 'l1', 'l2',
          'manhattan']

        - from scipy.spatial.distance: ['braycurtis', 'canberra', 'chebyshev',
          'correlation', 'dice', 'hamming', 'jaccard', 'kulsinski',
          'mahalanobis', 'matching', 'minkowski', 'rogerstanimoto',
          'russellrao', 'seuclidean', 'sokalmichener', 'sokalsneath',
          'sqeuclidean', 'yule']

        See the documentation for scipy.spatial.distance for details on these
        metrics:
        http://docs.scipy.org/doc/scipy/reference/spatial.distance.html

    metric_params : dict, optional (default=None)
        Additional keyword arguments for the metric function.

    contamination : float in (0., 0.5), optional (default=0.1)
        The amount of contamination of the data set, i.e. the proportion
        of outliers in the data set. When fitting this is used to define the
        threshold on the decision function.

    n_jobs : int, optional (default=1)
        The number of parallel jobs to run for neighbors search.
        If ``-1``, then the number of jobs is set to the number of CPU cores.
        Affects only :meth:`kneighbors` and :meth:`kneighbors_graph` methods.


    Attributes
    ----------
    negative_outlier_factor_ : numpy array, shape (n_samples,)
        The opposite LOF of the training samples. The lower, the more normal.
        Inliers tend to have a LOF score close to 1, while outliers tend
        to have a larger LOF score.

        The local outlier factor (LOF) of a sample captures its
        supposed 'degree of abnormality'.
        It is the average of the ratio of the local reachability density of
        a sample and those of its k-nearest neighbors.

    n_neighbors_ : integer
        The actual number of neighbors used for :meth:`kneighbors` queries.

    References
    ----------
    .. [1] Breunig, M. M., Kriegel, H. P., Ng, R. T., & Sander, J. (2000, May).
           LOF: identifying density-based local outliers. In ACM sigmod record.
    """
    def __init__(self, n_neighbors=20, algorithm='auto', leaf_size=30,
                 metric='minkowski', p=2, metric_params=None,
                 contamination=0.1, n_jobs=1):
        self._init_params(n_neighbors=n_neighbors,
                          algorithm=algorithm,
                          leaf_size=leaf_size, metric=metric, p=p,
                          metric_params=metric_params, n_jobs=n_jobs)

        self.contamination = contamination

    def fit_predict(self, X, y=None):
        """"Fits the model to the training set X and returns the labels
        (1 inlier, -1 outlier) on the training set according to the LOF score
        and the contamination parameter.


        Parameters
        ----------
        X : array-like, shape (n_samples, n_features), default=None
            The query sample or samples to compute the Local Outlier Factor
            w.r.t. to the training samples.

        Returns
        -------
        is_inlier : array, shape (n_samples,)
            Returns 1 for anomalies/outliers and -1 for inliers.
        """

        return self.fit(X)._predict()

    def fit(self, X, y=None):
        """Fit the model using X as training data.

        Parameters
        ----------
        X : {array-like, sparse matrix, BallTree, KDTree}
            Training data. If array or matrix, shape [n_samples, n_features],
            or [n_samples, n_samples] if metric='precomputed'.

        Returns
        -------
        self : object
            Returns self.
        """
        if not (0. < self.contamination <= .5):
            raise ValueError("contamination must be in (0, 0.5]")

        super(LocalOutlierFactor, self).fit(X)

        n_samples = self._fit_X.shape[0]
        if self.n_neighbors > n_samples:
            warn("n_neighbors (%s) is greater than the "
                 "total number of samples (%s). n_neighbors "
                 "will be set to (n_samples - 1) for estimation."
                 % (self.n_neighbors, n_samples))
        self.n_neighbors_ = max(1, min(self.n_neighbors, n_samples - 1))

        self._distances_fit_X_, _neighbors_indices_fit_X_ = (
            self.kneighbors(None, n_neighbors=self.n_neighbors_))

        self._lrd = self._local_reachability_density(
            self._distances_fit_X_, _neighbors_indices_fit_X_)

        # Compute lof score over training samples to define threshold_:
        lrd_ratios_array = (self._lrd[_neighbors_indices_fit_X_] /
                            self._lrd[:, np.newaxis])

        self.negative_outlier_factor_ = -np.mean(lrd_ratios_array, axis=1)

        self.threshold_ = -scoreatpercentile(
            -self.negative_outlier_factor_, 100. * (1. - self.contamination))

        return self

    def _predict(self, X=None):
        """Predict the labels (1 inlier, -1 outlier) of X according to LOF.

        If X is None, returns the same as fit_predict(X_train).
        This method allows to generalize prediction to new observations (not
        in the training set). As LOF originally does not deal with new data,
        this method is kept private.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features), default=None
            The query sample or samples to compute the Local Outlier Factor
            w.r.t. to the training samples. If None, makes prediction on the
            training data without considering them as their own neighbors.

        Returns
        -------
        is_inlier : array, shape (n_samples,)
            Returns -1 for anomalies/outliers and +1 for inliers.
        """
        check_is_fitted(self, ["threshold_", "negative_outlier_factor_",
                               "n_neighbors_", "_distances_fit_X_"])

        if X is not None:
            X = check_array(X, accept_sparse='csr')
            is_inlier = np.ones(X.shape[0], dtype=int)
            is_inlier[self._decision_function(X) <= self.threshold_] = -1
        else:
            is_inlier = np.ones(self._fit_X.shape[0], dtype=int)
            is_inlier[self.negative_outlier_factor_ <= self.threshold_] = -1

        return is_inlier

    def _decision_function(self, X):
        """Opposite of the Local Outlier Factor of X (as bigger is better,
        i.e. large values correspond to inliers).

        The argument X is supposed to contain *new data*: if X contains a
        point from training, it consider the later in its own neighborhood.
        Also, the samples in X are not considered in the neighborhood of any
        point.
        The decision function on training data is available by considering the
        opposite of the negative_outlier_factor_ attribute.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            The query sample or samples to compute the Local Outlier Factor
            w.r.t. the training samples.

        Returns
        -------
        opposite_lof_scores : array, shape (n_samples,)
            The opposite of the Local Outlier Factor of each input samples.
            The lower, the more abnormal.
        """
        check_is_fitted(self, ["threshold_", "negative_outlier_factor_",
                               "_distances_fit_X_"])

        X = check_array(X, accept_sparse='csr')

        distances_X, neighbors_indices_X = (
            self.kneighbors(X, n_neighbors=self.n_neighbors_))
        X_lrd = self._local_reachability_density(distances_X,
                                                 neighbors_indices_X)

        lrd_ratios_array = (self._lrd[neighbors_indices_X] /
                            X_lrd[:, np.newaxis])

        # as bigger is better:
        return -np.mean(lrd_ratios_array, axis=1)

    def _local_reachability_density(self, distances_X, neighbors_indices):
        """The local reachability density (LRD)

        The LRD of a sample is the inverse of the average reachability
        distance of its k-nearest neighbors.

        Parameters
        ----------
        distances_X : array, shape (n_query, self.n_neighbors)
            Distances to the neighbors (in the training samples `self._fit_X`)
            of each query point to compute the LRD.

        neighbors_indices : array, shape (n_query, self.n_neighbors)
            Neighbors indices (of each query point) among training samples
            self._fit_X.

        Returns
        -------
        local_reachability_density : array, shape (n_samples,)
            The local reachability density of each sample.
        """
        dist_k = self._distances_fit_X_[neighbors_indices,
                                        self.n_neighbors_ - 1]
        reach_dist_array = np.maximum(distances_X, dist_k)

        #  1e-10 to avoid `nan' when when nb of duplicates > n_neighbors_:
        return 1. / (np.mean(reach_dist_array, axis=1) + 1e-10)


# In[75]:

# predictor_keys = ['mean', 'expenses', 'sum', 'distance_traveled']
predictor_keys = ['expenses', 'distance_traveled']

model = LocalOutlierFactor(n_jobs=-1)
y = model.fit_predict(dataset_with_distances[predictor_keys])
model._predict([expected_abnormal_day[predictor_keys]])


# In[76]:

dataset_with_distances['lof_anomaly'] = y == -1
dataset_with_distances['lof_anomaly'].sum()


# In[77]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances,
           fit_reg=False,
           hue='lof_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# Let's see the results using just `distance_traveled` as predictor.

# In[78]:

predictor_keys = ['distance_traveled']

model = LocalOutlierFactor(contamination=.01, n_jobs=-1)
y = model.fit_predict(dataset_with_distances[predictor_keys])
model._predict([expected_abnormal_day[predictor_keys]])


# In[79]:

dataset_with_distances['lof_anomaly'] = y == -1
dataset_with_distances['lof_anomaly'].sum()


# In[80]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances.query('lof_anomaly'),
           fit_reg=False,
           hue='lof_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# The congresspeople ranking is similar to the one using standard deviation method.

# In[81]:

dataset_with_distances.query('lof_anomaly')     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# How about trying to combine standard deviation and Local Outlier Factor?

# In[82]:

to_show = dataset_with_distances['lof_anomaly'] &     dataset_with_distances['3_stds_anomaly']
sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances[to_show],
           fit_reg=False,
           hue='lof_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# In[83]:

dataset_with_distances[to_show].shape


# In[84]:

dataset_with_distances[to_show]


# In[85]:

dataset_with_distances['lof_anomaly'].describe()


# Number of cities may not be reflected in `distance_traveled` already. Let's see the differencies in the results.

# In[86]:

predictor_keys = ['distance_traveled', 'city']

model = LocalOutlierFactor(contamination=.01, n_jobs=-1)
y = model.fit_predict(dataset_with_distances[predictor_keys])
model._predict([expected_abnormal_day[predictor_keys]])


# In[87]:

dataset_with_distances['lof_anomaly'] = y == -1
dataset_with_distances['lof_anomaly'].sum()


# In[88]:

dataset_with_distances.query('lof_anomaly')     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# In[89]:

to_show = dataset_with_distances['lof_anomaly']
sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances[to_show],
           fit_reg=False,
           hue='lof_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# In[90]:

query = '(lof_anomaly == True) & (congressperson_name == "VANDERLEI MACRIS")'
dataset_with_distances.query(query).sort_values('issue_date', ascending=False).head()


# **So far, `IsolationForest` using `expenses` and `distance_traveled` as predictors seem to have best results for the purpose of this analysis**: allowing deputies to make many expenses (even expensive ones) and traveling through many cities in a single day, but questioning those making too many expenses without the excuse of a business trip.

# ## Deeper look into winner models
# 
# 5-stds and `IsolationForest` with `expenses/distance_traveled` as predictors and contamination of 0.1% return the best results. We need to compare them before going further.

# In[91]:

predictor_keys = ['expenses', 'distance_traveled']

forest_model = IsolationForest(contamination=.001, random_state=0)
forest_model.fit(dataset_with_distances[predictor_keys])


# In[92]:

dataset_with_distances.query('distance_traveled == {}'.format(dataset_with_distances['distance_traveled'].max()))


# In[93]:

isolation_ranking = dataset_with_distances.query('isolation_forest_anomaly')     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)
forest_anomaly_congresspeople = set(isolation_ranking['congressperson_name'])
len(forest_anomaly_congresspeople)


# In[94]:

stds_ranking = dataset_with_distances[dataset_with_distances['5_stds_anomaly']]     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)
stds_anomaly_congresspeople = set(stds_ranking['congressperson_name'])
len(stds_anomaly_congresspeople)


# Congresspeople who are both in `IsolationForest` and `5-stds` models:

# In[95]:

common_congresspeople = forest_anomaly_congresspeople & stds_anomaly_congresspeople
common_congresspeople


# Congresspeople who are just in `IsolationForest` or `5-stds` model:

# In[96]:

forest_anomaly_congresspeople ^ stds_anomaly_congresspeople


# In[97]:

congresspeople_ranking = pd.merge(isolation_ranking, stds_ranking,
                                  how='outer',
                                  on='congressperson_name',
                                  suffixes=('_isolation', '_stds'))


# In[98]:

congresspeople_ranking['isolation_stds_diff'] =     abs(congresspeople_ranking['abnormal_days_isolation'] -         congresspeople_ranking['abnormal_days_stds'])
congresspeople_ranking.head()


# In[99]:

congresspeople_ranking['ranking'] =     np.mean(congresspeople_ranking[['abnormal_days_isolation', 'abnormal_days_stds']], axis=1) - congresspeople_ranking['isolation_stds_diff']


# In[100]:

congresspeople_ranking.sort_values('ranking', ascending=False)


# In[101]:

is_in_both_models =     dataset_with_distances['congressperson_name'].isin(common_congresspeople) &     dataset_with_distances['5_stds_anomaly'] &     dataset_with_distances['isolation_forest_anomaly']
dataset_with_distances[is_in_both_models].sort_values('distance_traveled', ascending=False)


# In[102]:

dataset_with_distances['lof_and_5_stds'] = dataset_with_distances['isolation_forest_anomaly'] & dataset_with_distances['5_stds_anomaly']
dataset_with_distances['lof_or_5_stds'] = dataset_with_distances['isolation_forest_anomaly'] | dataset_with_distances['5_stds_anomaly']


# ### 5 standard deviations from the mean

# In[103]:

sns.lmplot('expenses', 'distance_traveled',
           data=dataset_with_distances,
           fit_reg=False,
           hue='5_stds_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# ### IsolationForest

# In[104]:

sns.lmplot('expenses', 'distance_traveled',
           data=dataset_with_distances,
           fit_reg=False,
           hue='isolation_forest_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# ### 5 standard deviations AND IsolationForest

# In[105]:

sns.lmplot('expenses', 'distance_traveled',
           data=dataset_with_distances,
           fit_reg=False,
           hue='lof_and_5_stds',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# ### 5 standard deviations OR IsolationForest

# In[106]:

sns.lmplot('expenses', 'distance_traveled',
           data=dataset_with_distances,
           fit_reg=False,
           hue='lof_or_5_stds',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# ## Anomalies in groups of days

# In[107]:

dataset['issue_date_day'] = dataset['issue_date'].apply(lambda date: date.day)
dataset['issue_date_month'] = dataset['issue_date'].apply(lambda date: date.month)
dataset['issue_date_year'] = dataset['issue_date'].apply(lambda date: date.year)
dataset['issue_date_weekday'] = dataset['issue_date'].apply(lambda date: date.weekday())
dataset['issue_date_week'] = dataset['issue_date'].apply(lambda date: date.week)


# In[108]:

# keys = ['applicant_id', 'issue_date_week', 'issue_date_year']
keys = ['congressperson_name', 'issue_date_week', 'issue_date_year']
aggregation_weeks = dataset.groupby(keys)['total_net_value'].     agg({'sum': np.sum, 'expenses': len, 'mean': np.mean})


# In[109]:

aggregation_weeks['expenses'] = aggregation_weeks['expenses'].astype(np.int)
aggregation_weeks.sort_values(['expenses', 'sum'], ascending=[False, False]).head(10)


# In[110]:

cities_weeks = dataset.groupby(keys)['city'].     agg({'city': lambda x: len(set(x)),
         'city_list': lambda x: ','.join(set(x))}
       ).sort_values('city', ascending=False)
cities_weeks.head()


# In[111]:

def calculate_sum_distances(x):
    coordinate_list = x[['latitude', 'longitude']].values
    edges = list(combinations(coordinate_list, 2))
    return np.sum([distance(edge[0][1:], edge[1][1:]).km for edge in edges])

distances_weeks = dataset.groupby(keys).apply(calculate_sum_distances)


# In[112]:

distances_weeks = distances_weeks.reset_index()     .rename(columns={0: 'distance_traveled'})     .sort_values('distance_traveled', ascending=False)
distances_weeks.head()


# In[113]:

aggregation_weeks = pd.merge(aggregation_weeks.reset_index(), cities_weeks.reset_index())


# In[114]:

dataset_with_distances_weeks =     pd.merge(aggregation_weeks,
             distances_weeks,
             left_on=keys,
             right_on=keys)
dataset_with_distances_weeks.sort_values(['distance_traveled', 'expenses'], ascending=[False, False]).head(10)


# In[115]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances_weeks,
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10,
           order=3)


# In[116]:

dataset_with_distances_weeks.describe()


# 4 "meals" every weekday

# In[117]:

dataset_with_distances_weeks[dataset_with_distances_weeks['expenses'] > 20].shape


# In[118]:

expenses_ceiling = dataset_with_distances_weeks['expenses'].mean() +     (5 * dataset_with_distances_weeks['expenses'].std())
distance_traveled_ceiling = dataset_with_distances_weeks['distance_traveled'].mean() +     (5 * dataset_with_distances_weeks['distance_traveled'].std())
is_anomaly = (dataset_with_distances_weeks['expenses'] > expenses_ceiling) &     (dataset_with_distances_weeks['distance_traveled'] > distance_traveled_ceiling)
dataset_with_distances_weeks[is_anomaly].shape


# In[119]:

expenses_ceiling, distance_traveled_ceiling


# In[120]:

dataset_with_distances_weeks[is_anomaly]     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_weeks'})     .sort_values('abnormal_weeks', ascending=False)     .head(10)


# In[121]:

dataset_with_distances_weeks['5_stds_anomaly'] = is_anomaly
dataset_with_distances_weeks['5_stds_anomaly'].sum() / len(dataset_with_distances_weeks)


# In[122]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances_weeks,
           fit_reg=False,
           hue='5_stds_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# In[123]:

predictor_keys = ['issue_date_week', 'issue_date_year', 'expenses', 'distance_traveled']

model = IsolationForest(contamination=.001, random_state=0)
model.fit(dataset_with_distances_weeks[predictor_keys])
y = model.predict(dataset_with_distances_weeks[predictor_keys])
dataset_with_distances_weeks['isolation_forest_anomaly'] = y == -1
dataset_with_distances_weeks['isolation_forest_anomaly'].sum()


# In[124]:

sns.lmplot('expenses', 'distance_traveled', 
           data=dataset_with_distances_weeks,
           fit_reg=False,
           hue='isolation_forest_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10)


# **Ideas**
# 
# * Come up with ways of giving a outlier-ness degree (i.e. how anomalous each day or week was).
# * Combine anomalous weeks with days. A anomalous day in a anomalous week has a higher outlier-ness degree.
# * Try linear regression as a Anomaly Detection method.

# ## Combining IsolationForest with hardcoded threshold

# In[125]:

expenses_threshold = dataset_with_distances['expenses'].mean() +     (10 * dataset_with_distances['expenses'].std())
dataset_with_distances['my_anomaly'] = dataset_with_distances['expenses'] > 8
dataset_with_distances['my_and_forest_anomaly'] =     dataset_with_distances['my_anomaly'] |     dataset_with_distances['isolation_forest_anomaly']
print(dataset_with_distances['my_anomaly'].sum())
sns.lmplot('expenses', 'distance_traveled',
           data=dataset_with_distances,
           hue='my_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           size=10,
           fit_reg=False)


# In[126]:

dataset_with_distances[dataset_with_distances['my_anomaly']]     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# ## Combining polynomial regression with hardcoded threshold
# 
# In fact, getting feedback from other people from the team, I came to the conclusion that the cases we want to report as "anomalies" are related with a regression.
# 
# First: cases with more than 8 meal receipts in a single day we want to get reported, doesn't matter the distance. Secondly: people traveling are expected to request for more meal reimbursements (e.g. coffee before going to the airport, something quick before checkin, more calm breakfast waiting for the flight... all of this in the same day, still legal), but many receipts in the same day, with short distance traveled is suspect. Still, too many receipts is still suspect. Thus what we expect is to form a regression, give an acceptable margin and consider everything outside, above and below it, suspect.

# In[127]:

to_plot = pd.DataFrame()
to_plot['x'] = dataset_with_distances['expenses'].astype(np.long)

fit = np.polyfit(to_plot['x'],
                 dataset_with_distances['distance_traveled'].astype(np.long),
                 3)
print(fit)
fit_fn = np.poly1d(fit)
to_plot['y'] = fit_fn(dataset_with_distances['expenses'])

sns.lmplot('x', 'y', 
           data=to_plot,
           scatter_kws={'marker': 'D',
                        's': 100},
           fit_reg=False,
           size=10)


# In[128]:

dataset_with_distances['expected_distance'] =     fit_fn(dataset_with_distances['expenses'])


# We want to limit the contamination to 0.1% (`diff_distance` approximately 3,000).

# In[129]:

expected_distances = dataset_with_distances['expected_distance']
diff_distance = abs(expected_distances - dataset_with_distances['distance_traveled'])

def contamination(threshold):
    return (diff_distance > threshold).sum() /         (len(dataset_with_distances) - dataset_with_distances['my_anomaly'].sum())

def threshold_for_contamination(expected_contamination):
    possible_thresholds = range(1, int(expected_distances.max()), 50)
    results = [(contamination(x), x) for x in possible_thresholds]
    best_choice = min(results, key=lambda x: abs(x[0] - expected_contamination))
    return best_choice[1]


# In[130]:

threshold_for_contamination(.001)


# In[131]:

dataset_with_distances['polyfit_anomaly'] =     diff_distance > threshold_for_contamination(.001)
dataset_with_distances['polyfit_anomaly'].sum()


# In[132]:

dataset_with_distances['my_and_polyfit_anomaly'] =     dataset_with_distances['my_anomaly'] |     dataset_with_distances['polyfit_anomaly']


# In[133]:

dataset_with_distances['my_and_polyfit_anomaly'].sum()


# In[134]:

sns.lmplot('expenses', 'distance_traveled',
           data=dataset_with_distances,
           hue='my_and_polyfit_anomaly',
           scatter_kws={'marker': 'D',
                        's': 100},
           fit_reg=False,
           size=10)


# In[135]:

dataset_with_distances.query('my_and_polyfit_anomaly & (expenses == 3)')


# In[136]:

dataset.query('(congressperson_name == "ROCHA") & (issue_date == "2015-06-19")')['document_id'].values


# In[137]:

dataset_with_distances.query('my_and_polyfit_anomaly')     .groupby('congressperson_name')['expenses'].count().reset_index()     .rename(columns={'expenses': 'abnormal_days'})     .sort_values('abnormal_days', ascending=False)     .head(10)


# In[138]:

dataset_with_distances.query('my_and_polyfit_anomaly')['expenses'].sum()


# In[139]:

dataset_with_distances.query('my_and_polyfit_anomaly')['sum'].sum()


# ## Conclusions
# 
# The results from "polyfit anomaly" don't necessarily mean anomalies, neither the final approach can really be consider a Anomaly Detection method. Yet is able to alert about a few cases deserving auditing and further investigation to prove illegal or immoral activities:
# 
# 1. Days with too many meal reimbursements/expenses. More than 8 meal reimbursuments in a single day is too suspicious.
# 2. Days with a large number of meal reimbursements without a travel to explain.
# 3. Days where the traveled distance is so big that it's suspicious by itself.
# 
# ---
# 
# [Ana Schwendler](https://github.com/anaschwendler) was my pair during a good portion of the time working on this analysis. [Felipe Cabral](https://github.com/cabral) also gave a nice guidance helping to define anomalous expenses and brainstorming approaches.

# In[ ]:



