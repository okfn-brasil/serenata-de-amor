
import wget 

import url_family_bag
import urllib
import os


count = 0
for url in url_family_bag.urls():
    print(url)    
    
    wget.download(url,"../data/file"+(str(count)))
    count = count + 1
        