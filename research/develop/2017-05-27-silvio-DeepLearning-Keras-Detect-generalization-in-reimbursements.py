
# coding: utf-8

# # Building powerful image classification using very little data
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
# # We will use the dataset of generalizations in reimbursements to train a Machine Learning model to predict those that are suspicious

# # First step: Directory to access the downloaded files

# In[ ]:

CONST_DIR = '../test/dataset/'

train_data_dir = CONST_DIR+'training/'
validation_data_dir = CONST_DIR+'validation/'

png_directory= CONST_DIR+'pos_validation/positive/'
png_directory=CONST_DIR+'pos_validation/negative/'

salve_model = '../test/model/'
if (not os.path.exists(salve_model)):
    os.mkdir(salve_model)


# In[1]:

from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras import backend as K
from keras.callbacks import ModelCheckpoint
import os
import os.path
import numpy as np

#fix random seed for reproducibility
seed = 2017
np.random.seed(seed)

nb_train_samples = sum([len(files) for r, d, files in os.walk(train_data_dir)])
nb_validation_samples = sum([len(files) for r, d, files in os.walk(validation_data_dir)])

print('no. of trained samples = ', nb_train_samples, ' no. of validation samples= ',nb_validation_samples)


#dimensions of our images.
img_width, img_height = 800, 600


epochs = 3 
batch_size = 2

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
checkpointer = ModelCheckpoint(filepath=os.path.join(salve_model,"weights.hdf5"), verbose=1, save_best_only=True)

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

# In[3]:

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

df1 = goldStandard(png_directory,1)
df2= goldStandard(png_directory,0)
frames = [df1, df2]
df = pd.concat(frames)
print(df.head())
print(df.tail())
test_model = load_model(filepath=os.path.join(salve_model,"weights.hdf5"))#I'm using the saved file to load the model

#dimensions of our images.
img_width, img_height = 800, 600
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

# In[4]:

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
# 
# # How to use it?
# 
# ### See this PULL Request : https://github.com/datasciencebr/rosie/pull/66

# In[ ]:



