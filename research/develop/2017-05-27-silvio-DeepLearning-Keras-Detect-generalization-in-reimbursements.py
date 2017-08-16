
# coding: utf-8

# # Building powerful image classification models using very little data
# 
# This notebook was based in this link:
# https://blog.keras.io/building-powerful-image-classification-models-using-very-little-data.html
# 
# They have good explanation and good images to show how these networks compute image classification.
# So, before to continue go there!
# Ps: I only commented in my code the strong changes regarding they example.
# 
# To use it i'm supposing you have installed the requirements to convert pdf to images.
# 
# ## Togheter with these previous requirements you have to install  Keras 2.0 API
# 
# ## Keras: Deep Learning library for TensorFlow and Theano
# https://github.com/fchollet/keras
# 
# 
# # Main constraint of this approach: We need a training and validation set :/ 
# 
# ## Solution >>> Let's build it.
# 
# 
# #### It is composed by 1691 wrong reimbursements, and 1691 not wrong (* they are called, positive, negative)
# 
# What i mean by wrong: http://www.camara.gov.br/cota-parlamentar/documentos/publ/2398/2015/5635048.pdf
# 
# As you can see it don't has any description about the consummation 
# 
# And what is "NOT WRONG": 
# 
# http://www.camara.gov.br/cota-parlamentar//documentos/publ/1773/2014/5506259.pdf
# 
# # All these reimbursements were validated by hand
# # Thanks so much everyone involved on it :D
# 
# Take a look at this great collaborative work: https://docs.google.com/spreadsheets/d/1o7P79iMw2VnJypSZNHrsDjud398g4vXpZdrGMMqe6qA/edit?usp=sharing
# 
# Here: you can find the up-to-date reimbursements
# https://drive.google.com/file/d/0B6F2XOmMAf28U1FsMTN0QXNPX28/view?usp=sharing
# 
# 
# ## PS: The first training set was also reevaluated after discussion with @anaschwendler
# ### In the spreadsheet they are in orange color.

# In[20]:

# First download the dataset
from serenata_toolbox.datasets import Datasets
datasets = Datasets('../test/')
datasets.downloader.download('2016-11-19-last-year.xz') 


# In[18]:

import os
import unicodedata
import shutil
from io import BytesIO
from urllib.request import urlopen

import numpy as np
import pandas as pd
from PIL import Image as pil_image
from wand.image import Image

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
        # Default arguments to read the file and has a good resolution
        with Image(file=response, resolution=300) as img:
            img.compression_quality = 99
            # Chosen format to convert pdf to image
            with img.convert('png') as converted:
                    converted.save(filename=file_name)
    except Exception as ex:
            print("Error during pdf download {}",url_link)
            print(ex)
            # Case we get some exception we return None
            return
        
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

# Reading the downloaded reimbursements files
data = pd.read_csv('../test/2016-11-19-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})

# Build the Directory structure for our ML model
CONST_DIR = '../test/dataset/'
directories = [CONST_DIR, CONST_DIR+'dataset/training',
                        CONST_DIR+'dataset/training/positive/',
                        CONST_DIR+'dataset/training/negative/',
                        CONST_DIR+'dataset/validation/',
                        CONST_DIR+'dataset/validation/positive/',
                        CONST_DIR+'dataset/validation/negative/',
                        CONST_DIR+'dataset/pos_validation/',
                        CONST_DIR+'dataset/pos_validation/positive/',
                        CONST_DIR+'dataset/pos_validation/negative/',
                        CONST_DIR+'save_model/']

for dirs in directories:
    if (not os.path.exists(dirs)):
        os.mkdir(dirs)


#I will look only the meals
data=data[data['subquota_description']=='Congressperson meal']

# Reference for our model.
link = 'https://drive.google.com/uc?export=download&id=0B6F2XOmMAf28OEdBLWVBZ2c1RVk'

response = urlopen(link)

csv_ref = pd.DataFrame.from_csv(response)
print(csv_ref.head(10))
print(csv_ref.shape)
doc_ids=[]

for index, refs in csv_ref.iterrows():
    full_name= refs['tocheck'].split("/")
    file_name = full_name[len(full_name)-1]
    doc_ids.append(file_name)
    
print ("recupered References: {}".format(len(doc_ids)))    

data=data[data['document_id'].isin(doc_ids)]
data['reference'] = csv_ref['standard']
data = __document_url(data)

for index, item in data.iterrows():
    file_name = item.document_id+'.png'
    if(item.reference == 1):
        file_name = os.path.join(positive, file_name)
        download_doc(item.link, file_name)
    else:
        file_name = os.path.join(negative, file_name)
        download_doc(item.link, file_name)
        
# Split our Files in Training, Validation and POS validation
# 70% tranning and 15% validation and 15% pos_validation


# In[4]:

from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras import backend as K
from keras.callbacks import ModelCheckpoint
import os.path
import numpy as np

#fix random seed for reproducibility
seed = 2017
np.random.seed(seed)

train_data_dir = '../test/dataset/training/'
validation_data_dir = '../test/dataset/validation/'



nb_train_samples = sum([len(files) for r, d, files in os.walk(train_data_dir)])
nb_validation_samples = sum([len(files) for r, d, files in os.walk(validation_data_dir)])

print('no. of trained samples = ', nb_train_samples, ' no. of validation samples= ',nb_validation_samples)


#dimensions of our images.
img_width, img_height = 800, 600


epochs = 20 
batch_size = 15

if K.image_data_format() == 'channels_first':
    input_shape = (3, img_width, img_height)
else:
    input_shape = (img_width, img_height, 3)

model = Sequential()
model.add(Conv2D(32, (3, 3), input_shape=input_shape))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(32, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(64, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Flatten())
model.add(Dense(64))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])

#this is the augmentation configuration we will use for training
train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=False)#As you can see i put it as FALSE and on link example it is TRUE
#Explanation, there no possibility to write in a reverse way :P

#this is the augmentation configuration we will use for testing:
#only rescaling
test_datagen = ImageDataGenerator(rescale=1. / 255)

train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='binary')

validation_generator = test_datagen.flow_from_directory(
    validation_data_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='binary')

#It allow us to save only the best model between the iterations 
checkpointer = ModelCheckpoint(filepath="weights.hdf5", verbose=1, save_best_only=True)

model.fit_generator(
    train_generator,
     callbacks=[checkpointer], #And we set the parameter to save only the best model
    steps_per_epoch=nb_train_samples // batch_size,
    epochs=epochs,
    validation_data=validation_generator,
    validation_steps=nb_validation_samples // batch_size)


# # Result: A network with 94% of accuracy!!! Big improvement regarding the first we buit...
# 
# 156/157 [============================>.] - ETA: 3s - loss: 0.3726 - acc: 0.8682 Epoch 00013: val_loss improved from 0.23616 to 0.22647, saving model to weights.hdf5
# 157/157 [==============================] - 607s - loss: 0.3715 - acc: 0.8691 - val_loss: 0.2265 - val_acc: 0.9423
# 
# # Let's use it on an external set of reimbursements!
# ### @vmesel recommended it, thanks for the feedback :D

# In[46]:

from keras.models import load_model
from keras.preprocessing.image import img_to_array, load_img
import glob
import numpy as np
import pandas as pd

def goldStandard(png_directory,value):
    png = glob.glob(png_directory+'*.png')
    data = list()
    for f in png:
        data.append(f)
    df = pd.DataFrame(data,columns=['Image'])
    df['Reference']=value
   
    return df

png_directory='../data/DeepLearningKeras/dataset/pos_validation/positive/'
df1 = goldStandard(png_directory,1)
png_directory='../data/DeepLearningKeras/dataset/pos_validation/negative/'
df2= goldStandard(png_directory,0)
frames = [df1, df2]
df = pd.concat(frames)
print(df.head())
print(df.tail())
test_model = load_model('./weights.hdf5')#I'm using the saved file to load the model

#dimensions of our images.
img_width, img_height = 300, 300
predicted=list()
for obj in df.iterrows():
    try:
        print(obj[1].Image)
        img = load_img(obj[1].Image,False,target_size=(img_width,img_height))#read a image
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0) #convert it
        preds = test_model.predict_classes(x) #predict it in our model :D
        prob = test_model.predict_proba(x) #get the probability of prediciton
        if(prob>=0.8 and preds==1):#Only keep the predictions with more than 80% of accuracy and the class 1 (suspicious)
            print("suspicious!!! prob:",prob)
            predicted.append(1)
        else:
            predicted.append(0)
    except Exception as ex:
            print(ex)
df['Predicted']=predicted


# # After to run the Model over the pos_validation set
# ## Let's verify how is the performance!

# In[47]:

from sklearn import metrics
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
from sklearn.metrics import roc_curve, auc

fpr, tpr, _= metrics.roc_curve(df.Reference,df.Predicted)
roc_auc = auc(fpr, tpr)
print("Confusion matrix")
print(metrics.confusion_matrix(df.Reference,df.Predicted))
print(" accuracy ",metrics.accuracy_score(df.Reference,df.Predicted))
print(" AUC ",roc_auc)
print(" precision ",metrics.precision_score(df.Reference,df.Predicted))
print(" recall ",metrics.recall_score(df.Reference,df.Predicted))
print(" f1-score ",metrics.f1_score(df.Reference,df.Predicted))


# # These results are amazing!! All metrics are above 91% !!
# 
# # Conclusion:
# ## We have a new classifier which detects generalization in the reimbursements
# 
# ## It handle with CEAP: Article 4, paragraph 3 (***Generalizations )
# The receipt or invoice must not have erasures, additions or amendments, must be dated and must list without generalizations or abbreviations each of the services or products purchased; it can be:
# 
# CEAP:
# 3. O documento que comprova o pagamento não pode ter rasura, acréscimos, emendas ou entrelinhas, deve conter data e deve conter os serviços ou materiais descritos item por item, sem generalizações ou abreviaturas, podendo ser:
# 
# 
# # How to use it?
# 
# ### See this PULL Request : https://github.com/datasciencebr/rosie/pull/66

# # PS: I would like to discuss some data in the train set
# 
# In the folder: "not wrong", the recipe: 5496084.pdf 
# 
# It is clear to me that the description of the items was made by someone else than the restaurant, is it allowed ???
# 
# Are the deputies or assessors changing a document?? What are the implications about it?
