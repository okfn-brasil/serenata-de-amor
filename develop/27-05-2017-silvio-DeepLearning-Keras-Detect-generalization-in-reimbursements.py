
# coding: utf-8

# # Building powerful image classification models using very little data
# 
# This notebook was based in this link:
# https://blog.keras.io/building-powerful-image-classification-models-using-very-little-data.html
# 
# They have good explanation and good images to show how these networks compute image classification.
# So, before to continue go there, I only comented the strong changes to make this method works to your case.
# 
# To use it, i'm suposing you already have instaled the requirements to convert pdf to images!
# 
# ## Togheter with these previous requirements you have to install  Keras 2.0 API
# 
# Wait.... Again more requirements...  What is Keras???
# 
# ## Keras: Deep Learning library for TensorFlow and Theano
# https://github.com/fchollet/keras
# 
# Yeap, let's include more functionalites in the serenata-de-amor :D
# 
# 
# # Main constraint of it
# 1) We need a training and validation set :/ 
# 
# 2) But deep learning needs a lot of data... *Read the title ;)
# 
# ## Solution >>> Let's build it.
# 
# Here:: you can find my training and validation set
# https://drive.google.com/file/d/0B6F2XOmMAf28dDZoOWtmS050Skk/view?usp=sharing
# 
# It is composed by 250 wrong reimbursiments, and 250 not wrong
# 
# What i mean by wrong: http://www.camara.gov.br/cota-parlamentar/documentos/publ/2398/2015/5635048.pdf
# 
# As you can see it don't has any description about the consumation 
# 
# And what is "NOT WRONG": 
# 
# http://www.camara.gov.br/cota-parlamentar//documentos/publ/1773/2014/5506259.pdf
# 
# 
# ## So Let's start to run our ML method (Remember to read the first link before to continue)

# In[9]:

from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras import backend as K
import os.path
import numpy as np

#fix random seed for reproducibility
seed = 2017
np.random.seed(seed)

train_data_dir = '../data/training set/ML/train'
validation_data_dir = '../data/training set/ML/validation'



nb_train_samples = sum([len(files) for r, d, files in os.walk(train_data_dir)])
nb_validation_samples = sum([len(files) for r, d, files in os.walk(validation_data_dir)])

print('no. of trained samples = ', nb_train_samples, ' no. of validation samples= ',nb_validation_samples)


#dimensions of our images.
img_width, img_height = 150, 150


epochs = 20 
batch_size = 3

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
    horizontal_flip=False)#As you can see i put it as FALSE and in the example link it is TRUE
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

model.fit_generator(
    train_generator,
    steps_per_epoch=nb_train_samples // batch_size,
    epochs=epochs,
    validation_data=validation_generator,
    validation_steps=nb_validation_samples // batch_size)

model.save_weights('first_try.h5')


# # Result: A network with 70% of accuracy, Not bad to our small sample...
# 
# # Let's use it on new reimbursements!
# 
# 
# 
# ## I did a little script which create this workflow: csv -> download -> convert to png
# ## the cell bellow do it

# In[10]:

# detect duplicate reimbursements
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import cv2
import urllib
import glob
from __future__ import print_function
from wand.image import Image

def convert_pdf_png_and_save(file_name,new_file_name):
    """Convert a pdf file to png and save it at disk

    arguments:
    file_name -- the real path to access the pdf file on disk
    new_file_name -- my_path/12312.png
    """
    try:
        #Default arguments to read the file and has a good resolution
        with Image(filename=file_name, resolution=300) as img:
            img.compression_quality = 99
            print('width =', img.width)
            print('height =', img.height)
            print('pages = ', len(img.sequence))
            print('resolution = ', img.resolution)

            #Format choosed to convert the pdf to image
            with img.convert('png') as converted:
                converted.save(filename=new_file_name)
                return 1
    except Exception as ex:
        print(ex)
        return 0
            
def downloadDoc(url,pdf_directory):
    """Download a pdf file to a specified directory 
    Returns the name of the file, e.g., 123123.pdf

    arguments:
    url -- the pdf url to chamber of deputies web site, e.g., http://www.../documentos/publ/2437/2015/5645177.pdf
    pdf_directory -- the path to save the file on disk
    
    Exception -- returns None
    """
    #using the doc id as file name
    full_name= url.split("/")
    file_name = full_name[len(full_name)-1]
    try:
        print (url)
        print (file_name)
        #open the resquest and get the file
        with urllib.request.urlopen(url) as response, open(pdf_directory+file_name, 'wb') as out_file:
            data = response.read()
            #write the file on disk
            out_file.write(data)
            # return the name 
            return out_file.name 
    except Exception as ex:
        return None #case we get some exception we return None

"""convert the row of a dataframe to a string represinting the url for the files in the chamber of deputies
        Return a string to access the files in the chamber of deputies web site
    
        arguments:
        record -- row of a dataframe
"""
def document_url(record):
    return 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/%s/%s/%s.pdf' %        (record['applicant_id'],record['year'], record['document_id'])

"""Download the files related to a dataframe and store them in an informed directory
        Returns the dataframe with the column filename filled
        arguments:
        sample -- the pandas dataframe
        pdf_directory -- base directory where we can access the file
"""  
def download_sample(sample,pdf_directory):
    for x in range(0,len(sample)):
        url = document_url(sample.iloc[x]) #get the url representation
        url = downloadDoc(url,pdf_directory) #download, store and get the file name
        if url != None :
            sample.iloc[x, sample.columns.get_loc('filename')]=url #fill the row with the filename

    
#Reading the reimbursements files
data = pd.read_csv('../data/2016-11-19-last-year.xz',
                   parse_dates=[16],
                   dtype={'document_id': np.str,
                          'congressperson_id': np.str,
                          'congressperson_document': np.str,
                          'term_id': np.str,
                          'cnpj_cpf': np.str,
                          'reimbursement_number': np.str})

#Directory where we will store the pdf downloaded OR where they already exist
pdf_directory="../data/pdfs/"

#I will look only the meals
data=data[data['subquota_description']=='Congressperson meal']

#creating a column to access the files latter
data['filename'] = ''
doc_ids=[]

#Get the pdfs files downloaded in our folder, e.g., /data
pdfs = glob.glob(pdf_directory+'*.pdf')

#Case we have pdf files we convert the pdf_files_name to doc_ids
for file in pdfs:
    full_name= file.split("/")
    file_name = full_name[len(full_name)-1]
    file_name= file_name.split(".pdf")
    file_name= file_name[0]
    doc_ids.append(file_name)
    
print ("recupered PDF files: {}".format(len(pdfs)))    

#Case we have pdf files we use them in our Machine learn method
if(len(pdfs)==0):
    data = data.sample(n=100)#Only 100 images to test (In my RUN i put 10000 YEAP, i will use them to refiny the training set)
    download_sample(data,pdf_directory)
else:
    data=data[data['document_id'].isin(doc_ids)]

#build a list of pdf_file_name to fill our dataframe directly
file_list = []
for x in range(0,len(data)):
    string = pdf_directory+"{}.pdf".format(data.iloc[x, data.columns.get_loc('document_id')])
    file_list.append(string)

data['filename']=file_list #fill it

file_png_list=[]
bad_index=[] #Bad requests to conversion which must be removed
for x in range(0,len(data)):
    if data.iloc[x]['filename']!="":
        #read the pdf file and convert to png
        newName=data.iloc[x, data.columns.get_loc('filename')]
        newName= newName.replace('.pdf','.png')
        converted = convert_pdf_png_and_save(data.iloc[x, data.columns.get_loc('filename')],newName)
        if(converted==1):
            file_png_list.append(newName)
        else:
            print("PNG failed removing index {}".format(x))
            bad_index.append(x)    

#remove bad requests            
data = data.drop(data.index[bad_index])
print("new dataframe len: {}".format(data.shape))

#Change the name of files
data['filename']=file_png_list


# # Here is where we play with our ML model
# 
# 1) Use the before trained network
# 
# 2) Get a new image and classify it as wrong or not
# 
# 3) Keep only predictions with more 80% probability
# 
# 4) Move it to another folder to future modifications
# 

# In[12]:

from keras.models import load_model
from keras.preprocessing.image import img_to_array, load_img
import shutil


#test_model = load_model('./first_try.h5')#I'm using the before model, if you want to load it from file use it
for png_file in file_png_list:
    try:
        img = load_img(png_file,False,target_size=(img_width,img_height))#read a iamge
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0) #convert it
        preds = model.predict_classes(x) #predict it in our model :D
        prob = model.predict_proba(x)
        if(prob>=0.8):#Only keep the predictions with more than 80% of accuracy
            shutil.move(png_file, '../data/toCheck2')
            print(data[data['filename']==png_file])
    except Exception as ex:


# # Results:
# 
# I got 2483 suspicious reimbursements. You can download them here:
# https://drive.google.com/file/d/0B6F2XOmMAf28eVBLUnRFQkZsSGs/view?usp=sharing
# 
# I will validate them by hand and use it to argument the the top layers of my pre-trained network.
# 
# # Conclusion
# 
# Using this method we can find a lot of suspicious reimbursements :) 
# Using this we created new pre-trained networks with few data :D
# 
# It seems that our deputies are used to ask for reimbursements with poor description, #CHATIADO
# 
# CEAP: 
# 
# O documento que comprova o pagamento não pode ter rasura, acréscimos, emendas ou entrelinhas, deve conter data e deve conter os serviços ou materiais descritos item por item, sem generalizações ou abreviaturas, podendo ser:
# 

# # PS: I would like to discuss some data in the train set
# 
# In the folder: "not wrong", the recipe: 5496084.pdf 
# 
# It is clear to me that the description of the items was made by someone else than the restaurant, is it allowed ???
# 
# Are the deputies or acessors changing a document?? What are the implications about it?

# In[ ]:



