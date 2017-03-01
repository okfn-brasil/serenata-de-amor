
# coding: utf-8

# In[1]:

import re

from IPython.display import HTML
import pandas as pd
import numpy as np

from serenata_toolbox.datasets import fetch

fetch("2017-02-15-receipts-texts.xz", "../data")
fetch("2016-12-06-reimbursements.xz", "../data")

def report(df):
    df = df.copy()
    df['receipt'] = df.apply(link_to_receipt, axis=1)
    df['document_id'] = df.apply(link_to_jarbas, axis=1)
    cols = ['document_id', 'receipt', 'issue_date', 'congressperson_name', 'total_net_value', 'supplier']
    return HTML(df[cols].to_html(escape=False))

def link_to_jarbas(r):
    return '<a target="_blank" href="http://jarbas.datasciencebr.com/#/document_id/{0}">{0}</a>'.format(r.document_id)

DOCUMENT_URL = (
    'http://www.camara.gov.br/'
    'cota-parlamentar/documentos/publ/{}/{}/{}.pdf'
)
def link_to_receipt(r):
    url = DOCUMENT_URL.format(r.applicant_id, r.year, r.document_id)
    return '<a target="_blank" href="{0}">RECEIPT</a>'.format(url)

pd.set_option('display.max_colwidth', 1500)


# In[2]:

texts = pd.read_csv('../data/2017-02-15-receipts-texts.xz', dtype={'text': np.str}, low_memory=False)
texts['text'] = texts.text.str.upper()

reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz', low_memory=False)
reimbursements = reimbursements.query('(subquota_description == "Congressperson meal") & (year >= 2015)')

data = texts.merge(reimbursements, on='document_id')


# In[3]:

print("Total meal reimbursements from 2015:", len(reimbursements))
print("Total meal reimbursements from 2015 that were OCRed:", len(data))
print("Total meal reimbursements from 2015 that were OCRed and have text:", len(data[~data.text.isnull()]))
data = data[~data.text.isnull()]


# Some of those reimbursements will have the remark value set to "discard" the value related to the alcoholic beverage so in order to make this initial analysis easier, we focus on those that does not have that value set

# In[4]:

data = data[data.remark_value == 0]
len(data)


# ## Reimbursements that have brazillian beer names in it

# In[5]:

report(data[data.text.str.contains('SKOL')])


# Only one of those reimbursements had an issue, looks like the others already disregarded the beer amounts even though the remark value is zeroed

# In[6]:

report(data[data.text.str.contains('BOHEMIA')])


# Both had the beers "deducted" even though there's no remark value

# In[7]:

report(data[data.text.str.contains('BRAHMA')])


# 2 of those had beers in them, one had the beer name on the restaurant name and the others disregarded the beers

# ## Reimbursements that have foreign beer names in them

# In[8]:

report(data[data.text.str.contains('HEINEKEN')])


# Out of nearly 40 reimbursements, 3 had beers in them and one of the reimbursements was already reported

# In[9]:

report(data[data.text.str.contains('BUDWEISER')])


# Only one with the beer without remark value that was already reported

# In[10]:

report(data[data.text.str.contains('STELLA ARTOIS')])


# None of them had issues

# ## Improving the algorithm
# 
# As we can see, lots of the reimbursements above did not have issues, it seems that (most of the times) whoever submitted the receipts already did the maths and removed the beer $$ from the reimbursement request. One idea of improving the accuracy of finding better cases would be to attempt to find the document total net value within the text of the receipt itself, meaning there is an alcoholic beverage within the receipt and everything bought was considered when the congressperson got reimbursed. Please note that this is a bad strategy for expenses made abroad because of the rate conversion.
# 
# In order to make things simpler, lets focus on reimbursements that are less than R$ 1.000,00. This is going to make the regular expression I'll use for matching easier on our eyes.

# In[11]:

data = data.query('total_net_value < 1000')


# In[12]:

def format_regex(val):
    hundreds = int(val)
    decimal = int((val * 100) % 100)
    if decimal == 0:
        decimal = '00'
    return '|'.join([
        '{},\s*{}'.format(hundreds, decimal),
        '{}\.\s*{}'.format(hundreds, decimal)
    ])

def receipt_matches_net_value(r):
    return any(re.findall(format_regex(r.total_net_value), r.text))

data = data[data.apply(receipt_matches_net_value, axis=1)]
len(data)


# Almost half matched, now we get the list of alcoholic beverages [put together by Irio Musskopf](https://github.com/datasciencebr/serenata-de-amor/blob/fb93f96e334c46f98eea3d4a9db565b8bc6bb45b/develop/2016-12-16-irio-alcohol-expenses.ipynb) and we search for the suspicious ones

# In[13]:

keywords = [
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
    'Casa Noble Reposado',
    'Casamigos',
    'Don Julio Blanco',
    'Patron Silver',
]
keywords_up = map(str.upper, keywords)
keywords_regex = '|'.join(keywords_up)

suspicious = data[data.text.str.contains(keywords_regex)]


# In[14]:

print(len(suspicious))
report(suspicious.head(10))


# None of the reimbursements above have alcoholic beverages in them, lets find out the matches

# In[15]:

suspicious.text.apply(lambda x: re.findall(keywords_regex, x)).head(10)


# Looks like `RUM` and `GIN` are not good words for this regex, lets wrap the keywords with whitespace separators

# In[16]:

def wrap(s):
    return '\s{}\s'.format(s.upper())
k = map(wrap, keywords)

keywords_regex = '|'.join(k)
keywords_regex

suspicious = data[data.text.str.contains(keywords_regex)]
print(len(suspicious))


# In[17]:

report(suspicious.head(10))


# None of the reimbursements above have alcoholic beverages in them, lets find out the matches

# In[18]:

suspicious.text.apply(lambda x: re.findall(keywords_regex, x)).head(10)


# - `GIN` really sucks because it can match with bad OCRed strings
# - `ANTARCTICA` can match with sodas / guaranás
# - `VINHO` is bad because it can match with dishes like "Filé ao molho de vinho"
# - The one that has `CHOPP` does not have a problem because the draft beer was not refunded, [the R\$117,00 net value of the reimbursement matched with the price of the dish that the congressperson ordered](http://www.camara.gov.br/cota-parlamentar/documentos/publ/1005/2015/5627118.pdf)
# 
# Lets look at the bottom of the dataset

# In[19]:

report(suspicious.tail(10))


# No bad reimbursements, lets look at matches one more time

# In[20]:

suspicious.text.apply(lambda x: re.findall(keywords_regex, x)).tail(10)


# ## Can we get to 100% accuracy?
# 
# Probably not, but lets try using some less ambiguous drinks

# In[21]:

keywords = [
    'cachaca',
    'cachaça',
    'cerveja',
    'champagne',
    'chope',
    'chopp',
    'conhaque',
    'liqueur',
    'tequila',
    'vodka',
    'whiskey',
    'whisky',
    'wine',
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
    'Casa Noble Reposado',
    'Casamigos',
    'Don Julio Blanco',
    'Patron Silver',
]
def wrap(s):
    return '\s{}\s'.format(s.upper())
k = map(wrap, keywords)
keywords_regex = '|'.join(k)
keywords_regex

suspicious = data[data.text.str.contains(keywords_regex)]
print(len(suspicious))


# In[22]:

report(suspicious)


# In[23]:

suspicious.text.apply(lambda x: re.findall(keywords_regex, x))


# Besides the same observations made on previous data, also found:
# - A few cases where beer / wine got canceled
#   - http://www.camara.gov.br/cota-parlamentar/documentos/publ/1947/2015/5643927.pdf
#   - http://www.camara.gov.br/cota-parlamentar/documentos/publ/2920/2015/5694874.pdf
#   - http://www.camara.gov.br/cota-parlamentar/documentos/publ/3071/2015/5705051.pdf
# - An [expense made abroad](http://www.camara.gov.br/cota-parlamentar/documentos/publ/2977/2015/5803734.pdf) that had many different things in it, not sure if the person did get reimbursed for a bud light or not
# - `POLAR` was a match with bad OCRed text as well
# - `CHAMPAGNE` can be used in sauces as well
# - `DEVASSA` can be the name of the restaurant like [this one](http://www.camara.gov.br/cota-parlamentar/documentos/publ/2267/2015/5830014.pdf)
# - `WINE` can be in the name of the restaurant like [this one](http://www.camara.gov.br/cota-parlamentar/documentos/publ/3037/2016/5973107.pdf)
# - Handwritten receipts might have keywords in them on random "marketing stuff" that gets written like `CERVEJA` in "A melhor casa da cerveja" in [this receipt](http://www.camara.gov.br/cota-parlamentar/documentos/publ/2990/2015/5813355.pdf)
# - "Comandas" might list all types of beverages they serve and could return lots of false positives like [this one](http://www.camara.gov.br/cota-parlamentar/documentos/publ/2295/2016/6067950.pdf)
# - 6 reimbursements had beers included but 4 of them were already identified and reported based on the previous results. The 2 new ones were also reported
#   
# ## Conclusions and thoughts
# 
# - Lots of reimbursements already exclude alcoholic beverages from the amount of returned even though there is no remark value
# - There are lots of false positives around, can we do something to get them out of the way?
# - Is this enough to incorporate this into rosie? How can we calculate scores for those reimbursements? Anything we can do to spot false positives and reduce the noise?
# - Are there better strategies for identifying these type of things besides OCR? Maybe some "advanced computer vision" tool / algorithm can yield better results
