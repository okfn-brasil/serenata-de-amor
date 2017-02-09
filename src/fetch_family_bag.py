

from urllib.request import urlretrieve

import url_family_bag

import os

BASE_DATA_DIR = '../data/file{0}{1}.zip'


for data in url_family_bag.urls():
    url, year, month =  data
    print (url,year,month)
    urlretrieve(url,BASE_DATA_DIR.format(year,month))
    
        