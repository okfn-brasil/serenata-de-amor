
# coding: utf-8

# # This python notebook only shows how to converte PDF files to PNG
# 
# ## To do so, 1) install the following requiriments:
# 
# ### In your linux distribution:
#     libmagickwand-dev ghostscript 
# 
# ### In your pip distribution:
#     wand==0.4.4
#     ghostscript==0.4.1
#     opencv3==3.2.0
#     
# # Case you are using the Dockerfile it is already there! 
# # Upload your image and Enjoy!!!

# In[1]:

get_ipython().magic('matplotlib inline')
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import cv2
import urllib
import glob


# In[20]:

#Let's load and save some pdf files
url = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/2437/2015/5645173.pdf'
file_name='5645173.pdf'
with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
    data = response.read() # a `bytes` object
    out_file.write(data)


# In[21]:

#Let's load and save some pdf files
url = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/2437/2015/5645177.pdf'
file_name='5645177.pdf'
with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
    data = response.read() # a `bytes` object
    out_file.write(data)


# In[4]:

print (glob.glob('5645173.pdf'))
print (glob.glob('5645177.pdf'))


# # Now let's convert the downloaded pdf to images

# In[8]:

from __future__ import print_function
from wand.image import Image

with Image(filename='5645173.pdf', resolution=300) as img:
    img.compression_quality = 99
    print('width =', img.width)
    print('height =', img.height)
    print('pages = ', len(img.sequence))
    print('resolution = ', img.resolution)

    with img.convert('png') as converted:
        converted.save(filename='5645173.png')
file_name1='5645173.png'


# In[9]:

from __future__ import print_function
from wand.image import Image

with Image(filename='5645177.pdf', resolution=300) as img:
    img.compression_quality = 99
    print('width =', img.width)
    print('height =', img.height)
    print('pages = ', len(img.sequence))
    print('resolution = ', img.resolution)

    with img.convert('png') as converted:
        converted.save(filename='5645177.png')
file_name2='5645177.png'


# ## Great they were converted!
# 
# # Let's use SIFT to extract features from these images!

# In[10]:

import cv2
import numpy as np

img = cv2.imread(file_name1)
gray=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
sift=cv2.xfeatures2d.SIFT_create()
kp=sift.detect(gray,None)
img=cv2.drawKeypoints(gray, kp, img,flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

cv2.imwrite('sift_keypoints.jpg',img)
plt.imshow(img,),plt.show()        


# In[11]:

import cv2
import numpy as np

img = cv2.imread(file_name2, 1)

gray=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
sift=cv2.xfeatures2d.SIFT_create()
kp=sift.detect(gray,None)
img=cv2.drawKeypoints(gray, kp, img,flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
cv2.imwrite('sift_keypoints2.jpg',img)

plt.imshow(img,),plt.show()


# # SIFT done! Go to our directory and check the generated files
# 
# ## Let's play with 2 images and see whether we can match common keypoints between them
# 
# ## I took the next algorithm from here:
# http://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_feature2d/py_feature_homography/py_feature_homography.html
# 

# In[12]:

img1 = cv2.imread(file_name1,0)          # queryImage
img2 = cv2.imread(file_name2,0) # trainImage

# Initiate SIFT detector
sift = cv2.xfeatures2d.SIFT_create()

# find the keypoints and descriptors with SIFT
kp1, des1 = sift.detectAndCompute(img1,None)
kp2, des2 = sift.detectAndCompute(img2,None)

# FLANN parameters
FLANN_INDEX_KDTREE = 0
index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
search_params = dict(checks=50)   # or pass empty dictionary

flann = cv2.FlannBasedMatcher(index_params,search_params)

matches = flann.knnMatch(des1,des2,k=2)

# Need to draw only good matches, so create a mask
matchesMask = [[0,0] for i in range(len(matches))]

# ratio test as per Lowe's paper
for i,(m,n) in enumerate(matches):
    if m.distance < 0.7*n.distance:
        matchesMask[i]=[1,0]

draw_params = dict(matchColor = (0,255,0),
                   singlePointColor = (255,0,0),
                   matchesMask = matchesMask,
                   flags = 0)

img3 = cv2.drawMatchesKnn(img1,kp1,img2,kp2,matches,None,**draw_params)
cv2.imwrite('macht_keypoints.jpg',img3)
plt.imshow(img3,),plt.show()        


# ## Great it works! We can work with these parsed images :D
# 
# ### So, following steps:
# 
# ### Goal: to build a ML classifier to detect duplicated reimbursiments.
# 
# ### I plain to follow  steps hereafter:
# 
# #### 1- Convert these pdfs to images
# #### 2- Extract SIFT features from them
# #### 3- Create a bag of visual words
# #### 4- Run a ML method to get the duplicated reimbursements
#             
#             
# ### !! What i have done so far !!
#     Steps 1 and 2 
#     For the nexts steps i will follow these approaches:
#     
#     http://www.robots.ox.ac.uk/~vgg/publications/2006/Sivic06c/sivic06c.pdf
#     
#     https://ianlondon.github.io/blog/how-to-sift-opencv/
#     
#     ### I did something similar before. Where i got the Scenes of a movie using an image as input
#     ### I coded it on matlab, so i can't to use it here directly.
#     ### However, i noticed some good code on github which we can adapt to our problem:
#     ### Look at my repository: 
#     https://github.com/silviodc/general_img_classifier
#     https://github.com/silviodc/Bag-of-Visual-Words-Python
#     
# ### My main concerns about to use only the images are:
# ##### The recuperation of similar images refering to diferent reimbursements.
# ##### --- It can be from any politician, 
# #### ---- I guess our approach must to preserve for more precision at the begining (*It is good to market )
# 
# ### About these similar images check the issue: https://github.com/datasciencebr/serenata-de-amor/issues/32
# ##### ---- So, i also will try to combine the sift descriptors and other information. 
# 

# In[ ]:



