
# coding: utf-8

# # Comparison between Chamber of Deputies CEAP datasets 1.0 and 2.0
# 
# This notebook compares the old Chamber's CEAP dataset (the huge XML files) with the new one (CSV by year). The main objective of this comparison is to show we didn't lose any data on the migration from the 1.0 to the much more efficient 2.0 version of the data. This validates changes to serenata-toolbox so we can ditch 1.0 datasets for good and be prepare to their extinction by the Chamber's Open Data team.
# 
# Let's begin by loading both old and new datasets
# 

# In[1]:

import pandas as pd

pd.set_option('max_columns', 500)


# In[2]:

from serenata_toolbox.datasets import Datasets

datasets = Datasets('../data')
datasets.downloader.download('2017-05-21-reimbursements.old.xz')
datasets.downloader.download('2017-05-21-reimbursements.new.xz')


# In[3]:

old_dataset = pd.read_csv('../data/2017-05-21-reimbursements.old.xz',
                        compression='xz',
                        low_memory=False)


# In[4]:

new_dataset = pd.read_csv('../data/2017-05-21-reimbursements.new.xz',
                        compression='xz',
                        low_memory=False)


# First we need to check if both datasets have the same columns, even in they are in the same order:

# In[5]:

old_keys = old_dataset.keys()
new_keys = new_dataset.keys()

print(old_keys==new_keys)


# We can also make sure they have the same types for all columns

# In[6]:

new_dataset.dtypes == old_dataset.dtypes


# Now we can take a slice of the datasets by year and compare their sizes. We also remove the current year, because this ongoing registry seems to have different update pace between versions, so it makes no sense comparing them:

# In[7]:

old_dataset = old_dataset[old_dataset['year'] != 2017]
new_dataset = new_dataset[new_dataset['year'] != 2017]

for year in pd.unique(old_dataset['year']):
    old_size = len(old_dataset[old_dataset['year']==year])
    new_size = len(new_dataset[new_dataset['year']==year])
    print('year: {} old: {} new: {} diff: {}'.format(year, old_size, new_size, new_size-old_size))


# Oddly enough, there is a single row missing in the new dataset. Let's find out which document is that and also make sure the exact document_ids are present in both datasets:

# In[8]:

new_docs = list(new_dataset['document_id'])
old_docs = list(old_dataset['document_id'])

old_extra = list(set(old_docs) - set(new_docs))
print('Extra documents found in old dataset: {}'.format(len(old_extra)))

new_extra = list(set(new_docs) - set(old_docs))
print('Extra documents found in new dataset: {}'.format(len(new_extra)))


# So there is really only one inconsistency between datasets. A quick query can show us the culprit:

# In[9]:

old_dataset[old_dataset['document_id'].isin(old_extra)]


# Checking the CSV file for year 2016 in the 2.0 version of the data, this document_id 6271581 is really missing, so it's not a parse problem on our side. An email was sent to Camara's Open Data team so we can understand what is happening.
