
# coding: utf-8

# # Hello World
# 
# This notebook walks through basic code examples for integrating various packages with Neo4j, including `py2neo`, `ipython-cypher`, `pandas`, `networkx`, `igraph`, and `jgraph`.

# # py2neo
# 
# `py2neo` is one of Neo4j's Python drivers. It offers a fully-featured interface for interacting with your data in Neo4j. Install `py2neo` with `pip install py2neo`.

# ## Connect
# 
# Connect to Neo4j with the `Graph` class.

# In[23]:

from py2neo import Graph

graph = Graph()


# In[24]:

graph.delete_all()


# ## Nodes
# 
# Create nodes with the `Node` class. The first argument is the node's label. The remaining arguments are an arbitrary amount of node properties or key-value pairs.

# In[25]:

from py2neo import Node

nicole = Node("Person", name="Nicole", age=24)
drew = Node("Person", name="Drew", age=20)

mtdew = Node("Drink", name="Mountain Dew", calories=9000)
cokezero = Node("Drink", name="Coke Zero", calories=0)

coke = Node("Manufacturer", name="Coca Cola")
pepsi = Node("Manufacturer", name="Pepsi")

graph.create(nicole | drew | mtdew | cokezero | coke | pepsi)


# In[26]:

from scripts.vis import draw

options = {"Person": "name", "Drink": "name", "Manufacturer": "name"}
draw(graph, options, graph_name="Example 1")


# P.S. - If you want to check out what's going on behind the scenes for the `draw()` function used above, take a look at [`scripts/vis.py`](https://github.com/nicolewhite/neo4j-jupyter/blob/master/scripts/vis.py).

# ## Relationships
# 
# Create relationships between nodes with the `Relationship` class.

# In[27]:

from py2neo import Relationship

graph.create(Relationship(nicole, "LIKES", cokezero))
graph.create(Relationship(nicole, "LIKES", mtdew))
graph.create(Relationship(drew, "LIKES", mtdew))
graph.create(Relationship(coke, "MAKES", cokezero))
graph.create(Relationship(pepsi, "MAKES", mtdew))

draw(graph, options, graph_name="Example 2")


# ## Cypher
# 
# Retrieve Cypher query results with `Graph.cypher.execute`.

# In[28]:

query = """
MATCH (person:Person)-[:LIKES]->(drink:Drink)
RETURN person.name AS name, drink.name AS drink
"""

data = graph.run(query)

for d in data:
    print(d)


# ## Parameterized Cypher
# 
# Pass parameters to Cypher queries by passing additional key-value arguments to `Graph.cypher.execute.` Parameters in Cypher are named and are wrapped in curly braces.

# In[29]:

query = """
MATCH (p:Person)-[:LIKES]->(drink:Drink)
WHERE p.name = {name}
RETURN p.name AS name, AVG(drink.calories) AS avg_calories
"""

data = graph.run(query, name="Nicole")

for d in data:
    print(d)


# # ipython-cypher
# 
# `ipython-cypher` exposes `%cypher` magic in Jupyter. Install `ipython-cypher` with `pip install ipython-cypher`.

# In[30]:

get_ipython().magic('load_ext cypher')


# ## Cypher
# 
# `%cypher` is intended for one-line Cypher queries and `%%cypher` is intended for multi-line Cypher queries. Placing `%%cypher` above a Cypher query will display that query's results.

# In[31]:

get_ipython().run_cell_magic('cypher', '', 'MATCH (person:Person)-[:LIKES]->(drink:Drink)\nRETURN person.name, drink.name, drink.calories')


# ## Pandas Data Frames
# 
# Cypher query results can be coerced to `pandas` data frames with the `get_dataframe` method. To assign Cypher query results to a variable, you need to use `%cypher` and separate lines with \\. You'll first need to install `pandas` with `pip install pandas`.

# In[32]:

results = get_ipython().magic('cypher MATCH (person:Person)-[:LIKES]->(drink:Drink)                   RETURN person.name AS name, drink.name AS drink')
    
df = results.get_dataframe()

df


# In[33]:

df.index


# In[34]:

df.iloc[[1]]


# In[35]:

df["name"]


# ## NetworkX Graphs
# 
# Cypher query results can be coerced to `NetworkX` MultiDiGraphs, graphs that permit multiple edges between nodes, with the `get_graph` method. You'll first need to install `NetworkX` with `pip install networkx`.

# In[36]:

import networkx as nx
get_ipython().magic('matplotlib inline')

results = get_ipython().magic('cypher MATCH p = (:Person)-[:LIKES]->(:Drink) RETURN p')

g = results.get_graph()

nx.draw(g)


# In[37]:

g.nodes(data=True)


# In[38]:

nx.degree(g)


# # igraph
# 
# Cypher query results can be imported into `igraph` with `py2neo`. You'll need to install `igraph` with `pip install python-igraph`. Query results should be returned as edgelists, as `igraph` has a method for building an `igraph` object from a list of tuples representing edges between nodes.

# In[17]:

from py2neo import Graph as PGraph
from igraph import Graph as IGraph

neo4j = PGraph()

query = """
MATCH (person:Person)-[:LIKES]->(drink:Drink)
RETURN person.name AS source, drink.name AS target
"""

data = neo4j.run(query)
tups = []

for d in data:
    tups.append((d["source"], d["target"]))


# In[18]:

ig = IGraph.TupleList(tups)

ig


# In[19]:

best = ig.vs.select(_degree = ig.maxdegree())["name"]
best


# # jgraph
# 
# `jgraph` will plot tuple lists as 3D graphs.

# In[17]:

import jgraph

jgraph.draw([(1, 2), (2, 3), (3, 4), (4, 1), (4, 5), (5, 2)])


# In[18]:

data = graph.run("MATCH (n)-->(m) RETURN ID(n), ID(m)")
data = [tuple(x) for x in data]

jgraph.draw(data)


# In[ ]:




# In[ ]:



