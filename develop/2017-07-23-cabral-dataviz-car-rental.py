
# coding: utf-8

# # Data Visualization on Car rental made by congressperson

# In[1]:


import numpy as np
import pandas as pd

from bokeh.io import curdoc, output_file, show, 
from bokeh.layouts import widgetbox, row
from bokeh.models import CategoricalColorMapper, ColumnDataSource, HoverTool, Select, Slider 
from bokeh.plotting import figure 


# In[2]:


reimbursements = pd.read_csv(
    '../data/2017-07-04-reimbursements.xz',
    dtype={'cnpj_cpf': np.str},
    low_memory=False
)
reimbursements.shape


# In[5]:


reimbursements.head(1)


# In[6]:


keys = ['subquota_number', 'subquota_description']
reimbursements[keys].groupby(keys).count().reset_index()


# In[7]:


consultancies = reimbursements[reimbursements.subquota_number == 15]
consultancies.shape


# In[8]:


consultancies.head(1)


# In[ ]:




