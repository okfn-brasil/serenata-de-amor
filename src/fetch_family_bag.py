
import wget 

import url_family_bag
import urllib
import os


count = 0
for url in url_family_bag.urls():
        wget.download(url,"../data/file"+(str(count)))
    
        