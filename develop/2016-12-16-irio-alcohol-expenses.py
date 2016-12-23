
# coding: utf-8

# In[12]:

sc.parallelize([1, 2, 3]).map(lambda x: x).collect()


# In[2]:

drinks_and_brands = {
  'drinks': {
    'beer',
    'brandy',
    'cachaca',
    'cachaça',
    'cerveja',
    'champagne',
    'chope',
    'chopp',
    'conhaque',
    'gim',
    'gin',
    'liqueur',
    'pint',
    'rum',
    'tequila',
    'vinho',
    'vodka',
    'whiskey',
    'whisky',
    'wine',
  },
  'wines': {
    'Albarino',
    'Barbera',
    'Bonarda',
    'Cabernet Franc',
    'Cabernet Sauvignon',
    'Chardonnay',
    'Chenin Blanc',
    'Garnacha',
    'Gewurztraminer',
    'Grenache',
    'Malbec',
    'Merlot',
    'Moscato',
    'Nebbiolo',
    'Palomino',
    'Pinot Grigio',
    'Pinot Noir',
    'Pinotage',
    'Riesling',
    'Sangiovese',
    'Sauvignon Blanc',
    'Shiraz',
    'Sylvaner',
    'Syrah',
    'Tempranillo',
    'Viognier',
    'Zinfandel',
  },
  'wine_brands': {
    'Aquitania Sol',
    'Beringer',
    'Blossom hill',
    'Casa Marín',
    'Casa Postal',
    'Casas Del Bosque',
    'Concha Y Toro',
    'Coronas',
    'Gallo',
    'Hardys',
    'House Malmau',
    'Jacobs Creek',
    'Lindemans',
    'Mil Piedras',
    'Ochotierras',
    'Paula Laureano',
    'Sutter Home',
    'Trumpeter',
    'Vila Regia',
    'Vinzelo',
    'Weinert',
    'Yellow tail',
  },
  'beer_brands': {
    'Antarctica',
    'Antartica',
    'Becks',
    'Bohemia',
    'Brahma',
    'Bucanero',
    'Bud Light',
    'Budweiser',
    'Caracu',
    'Coors Light',
    'Corona',
    'Devassa',
    'Franziskaner',
    'Guiness',
    'Harbin',
    'Heineken',
    'Hertog Jan',
    'Hoegaarden',
    'Itaipava',
    'Kaiser',
    'Leffe',
    'Lowenbrau',
    'Miller Light',
    'Nortena',
    'Nortenã',
    'Nova Schin',
    'Polar',
    'Quilmes',
    'Serramalte',
    'Skol',
    'Stella Artois',
    'Yanjing',
  },
  'vodka_brands': {
    'Absolut',
    'Balalaika',
    'Blue Spirit Unique',
    'Hangar One',
    'Imperia',
    'Jean Mark XO',
    'Kadov',
    'Komaroff',
    'Kovak',
    'Leonoff',
    'Moscowita',
    'Natasha',
    'Orloff',
    'Roth California',
    'Skyy90',
    'Smmirnoff',
    'Ultimat',
    'Xellent',
    'Zvonka Dubar',
  },
  'whisky_brands': {
    'Ardbeg',
    'Bagpiper',
    'Ballantine’s',
    'Ballantines',
    'Bushmills',
    'Campari',
    'Chivas',
    'Forty Creek',
    'Glenlivet',
    'Glenmorangie',
    'Imperial Blue',
    'Jack Daniel’s',
    'Jack Daniels',
    'Jameson',
    'Johnnie Walker',
    'McDowell',
    'McDowell’s',
    'Old Tavern',
    'Royal Salute',
    'Royal Stag',
    'Wild Turkey',
  },
  'tequila': {
    'Casa Noble Reposado',
    'Casamigos',
    'Don Julio Blanco',
    'Patron Silver',
  }
}


# In[7]:

import itertools
keywords = set(itertools.chain(*drinks_and_brands.values()))


# In[8]:

import unicodedata

def normalize_string(string):
    if isinstance(string, str):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')


# In[9]:

keywords = set(map(normalize_string, keywords))


# ## Convert PDFs to text

# In[52]:

import glob
import os.path
from PIL import Image
from pytesseract import image_to_string
import subprocess

receipt_paths = glob.glob('../data/receipts/**/*.pdf', recursive=True)

def pdf_to_image(input_path):
    output_path = input_path.replace('pdf', 'png')
    if not os.path.exists(output_path):
        subprocess.call(['sips', '-s', 'format', 'png',
                         input_path, '--out', output_path])
    return output_path

sc.parallelize(receipt_paths)     .map(pdf_to_image)     .count()
#     .map(image_to_text) \
#     .map(normalize_string) \
#     .filter(lambda text: any(keywords & set(text.split(' ')))) \


# In[34]:

string = 'fdsfsd fsdf sdf fof far fabzar l'
any(keyword in string for keyword in {'foo', 'bar', 'fabzar l'})


# In[58]:

from pytesseract import image_to_string

receipt_paths = glob.glob('../data/receipts/**/*.png', recursive=True)

def image_to_text(input_path, psm='6'):
    print(input_path)
    return image_to_string(Image.open(input_path),
                           config='-psm {}'.format(psm))

def contains_keyword(text):
    return any(key in text for key in keywords)


sc.parallelize(receipt_paths)     .map(lambda path: (path, image_to_text(path)))     .mapValues(normalize_string)     .filter(lambda path_text: contains_keyword(path_text[1]))     .collect()
#     .map(lambda path_text: path_text[0]) \


# In[68]:

[x[0][3:] for x in _58[13:]]


# In[ ]:



