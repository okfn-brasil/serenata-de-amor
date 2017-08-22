
# coding: utf-8

# 
# ## According to CEAP: Article 4, paragraph 3 
# 
# The receipt or invoice must not have erasures, additions or amendments, must be dated and must list without generalizations or abbreviations each of the services or products purchased; it can be:
# 
# CEAP:
# 3. O documento que comprova o pagamento não pode ter rasura, acréscimos, emendas ou entrelinhas, deve conter data e deve conter os serviços ou materiais descritos item por item, sem generalizações ou abreviaturas, podendo ser:
# 
# 
# # Sumarizing, the reimbursements can not have (***Generalizations )
# 
# What i mean by generalization:
# http://www.camara.gov.br/cota-parlamentar/documentos/publ/2398/2015/5635048.pdf
# 
# As you can see it doesn't has any description about the consummation 
# 
# And what is not a generalization? 
# 
# http://www.camara.gov.br/cota-parlamentar//documentos/publ/1773/2014/5506259.pdf
# 
# 
# # Therefore, the goal of this notebook is to build a dataset to train Machine Learn methods to detect generalizations in reimbursements 
# 
# 
# # To this task we built a  gold standard reference containing:
# 
# 1) 1691 reimbursements with generalized descriptions
# 2) 1691 well described (* they are called, positive, negative)
# 
# # All these reimbursements were validated by hand
# # Thanks so much everyone involved on it :D
# 
# https://drive.google.com/file/d/0B6F2XOmMAf28U1FsMTN0QXNPX28/view?usp=sharing

# # Necessary imports

# In[1]:

import os
import unicodedata
import shutil
import random
import glob
import re
import numpy as np
import pandas as pd
import os.path

from io import BytesIO
from urllib.request import urlopen
from tqdm import tqdm
from PIL import Image as pil_image
from wand.image import Image
from serenata_toolbox.datasets import Datasets


# # Lets start downloading the reimbursements from the toolbox 

# In[2]:


datasets = Datasets('../test/')
datasets.downloader.download('2016-11-19-last-year.xz') 


# # Then we read the downloaded reimbursements

# In[3]:

# Reading the downloaded reimbursements files
data = pd.read_csv('../test/2016-11-19-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})


# # Next step build the folder structure 
# 
# 

# In[4]:

# Build the Directory structure for our ML model
CONST_DIR = '../test/dataset/'
directories = [CONST_DIR, CONST_DIR+'training',
                        CONST_DIR+'training/positive/',
                        CONST_DIR+'training/negative/',
                        CONST_DIR+'validation/',
                        CONST_DIR+'validation/positive/',
                        CONST_DIR+'validation/negative/',
                        CONST_DIR+'pos_validation/',
                        CONST_DIR+'pos_validation/positive/',
                        CONST_DIR+'pos_validation/negative/']

for dirs in directories:
    if (not os.path.exists(dirs)):
        os.mkdir(dirs)
        
positive = directories[2]
negative = directories[3]


# # Download the csv file containing the references

# In[5]:


link = 'https://drive.google.com/uc?export=download&id=0B6F2XOmMAf28OEdBLWVBZ2c1RVk'

response = urlopen(link)

csv_ref = pd.DataFrame.from_csv(response)
print(csv_ref.head(10))
print(csv_ref.shape)


# # Filter the reimbursements from the toolbox to be aligned to our reference

# In[6]:

doc_ids=[]
for index, refs in csv_ref.iterrows():
    full_name= refs['tocheck'].split("/")
    file_name = full_name[len(full_name)-1]
    doc_ids.append(file_name)
    
print ("recupered References: {}".format(len(doc_ids)))    
csv_ref['id'] = doc_ids
data=data[data['document_id'].isin(doc_ids)]

refs=[]
for index, item in tqdm(data.iterrows()):
        tmp = csv_ref.loc[csv_ref['id'] == item.document_id]['standard']
        refs.append(tmp.values[0])
data['reference'] = refs
print(len(data[data['reference']==1]))
print(len(data[data['reference']==0]))


# # Build a direct link to PDFs

# In[7]:

""" Creates a new column 'links' containing an url
        for the files in the chamber of deputies website
        Return updated Dataframe
        arguments:
        record -- Dataframe
"""       
def __document_url(X):
    X['link'] = ''
    links = list()
    for index, x in X.iterrows():
        base = "http://www.camara.gov.br/cota-parlamentar/documentos/publ"
        url = '{}/{}/{}/{}.pdf'.format(base, x.applicant_id, x.year, x.document_id)
        links.append(url)
    X['link'] = links
    return X


data = __document_url(data)


# # Download the PDFs and convert them to PNG

# In[8]:

# Case you DO NOT WANT to download all dataset set STOP_AFTER bigger than 0 and lower than 1600. 
# It will download the same amount for positive and negative samples
# Case you WANT all put 0
STOP_AFTER = 30


# In[9]:

"""Download a pdf file and transform it to png
        arguments:
        url -- the url to chamber of deputies web site, e.g.,
        http://www.../documentos/publ/2437/2015/5645177.pdf
        file_name -- myDirectory/5645177.png
        Exception -- returns None
"""
def download_doc(url_link, file_name):
    try:
        # Open the resquest and get the file
        response = urlopen(url_link)
        if (response is not None):
            # Default arguments to read the file and has a good resolution
            with Image(file=response, resolution=300) as img:
                img.compression_quality = 99
                # Chosen format to convert pdf to image
                with img.convert('png') as converted:
                        converted.save(filename=file_name)
                        return True
        else:
            return None
    except Exception as ex:
            print("Error during pdf download {}",url_link)
            print(ex)
            # Case we get some exception we return None
            return None
        
def download():
    for index, item in tqdm(data.iterrows()):
        file_name = item.document_id+'.png'
        if(item.reference == 1):
            file_name = os.path.join(positive, file_name)
            request = download_doc(item.link, file_name)
        else:
            file_name = os.path.join(negative, file_name)
            request = download_doc(item.link, file_name)
    
if(STOP_AFTER != 0 and STOP_AFTER<1690): 
    tmp_pos = data[data['reference']==1]
    print("POSITIVE: ",tmp_pos.shape)
    tmp_pos = tmp_pos.sample(STOP_AFTER)
    tmp_neg = data[data['reference']==0]
    print("NEGATIVE: ",tmp_neg.shape)
    tmp_neg = tmp_neg.sample(STOP_AFTER)
    
    data = pd.concat([tmp_pos,tmp_neg])
    download()
else:
    download()


# # Split our data in
# 
# ### 70 % of reimbursements for training
# ### 15 % for validation
# ### 15 % for pos validation

# In[10]:

def split_data(len_samples,directory_src,directory_dest):
    for x in range(1,len_samples):
        current_files = glob.glob(directory_src+'*.png')
        file_name = re.sub(directory_src, r'', current_files[0])
        shutil.move(os.path.join(directory_src, file_name),  os.path.join(directory_dest, file_name))

# Split our Files in Training, Validation
# 70% tranning and 30% validation
len_val_positive = int(len(glob.glob(positive+'*.png'))*0.3)
len_val_negative = int(len(glob.glob(negative+'*.png'))*0.3)

split_data(len_val_positive,positive,directories[5])
split_data(len_val_negative,negative,directories[6])

# Split the Validation in 2 for POS validation
len_val_positive = int(len(glob.glob(directories[5]+'*.png'))/2)
len_val_negative = int(len(glob.glob(directories[6]+'*.png'))/2)

split_data(len_val_positive,directories[5],directories[8])
split_data(len_val_negative,directories[6],directories[9])


# # Lets verify how much data we have

# In[11]:

train_data_dir = CONST_DIR+'training'
validation_data_dir =  CONST_DIR+'validation'
pos_validation_data_dir = CONST_DIR+'pos_validation'


nb_train_samples = sum([len(files) for r, d, files in os.walk(train_data_dir)])
nb_validation_samples = sum([len(files) for r, d, files in os.walk(validation_data_dir)])
nb_pos_validation_samples = sum([len(files) for r, d, files in os.walk(pos_validation_data_dir)])

print('no. of trained samples = ', nb_train_samples)
print('no. of validation samples= ',nb_validation_samples)
print('no. of pos validation samples= ',nb_pos_validation_samples)



# In[ ]:



