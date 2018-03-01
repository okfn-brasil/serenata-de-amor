
# coding: utf-8

# # Meals for kids
# 
# Rosie already has a way to detect meal price outliers based on other reimbursements made on the same restaurant. Now that we have a new dataset with receipts OCRed texts we can use the information on meals paid for kids in order to increase its probability of being meals paid for other people.
# 
# 
# ## Data preparation

# In[1]:

import re

from IPython.display import HTML
import pandas as pd
import numpy as np

from serenata_toolbox.datasets import fetch

def report(df):
    df = df.copy()
    df['receipt'] = df.apply(link_to_receipt, axis=1)
    df['document_id'] = df.apply(link_to_jarbas, axis=1)
    cols = ['document_id', 'receipt', 'issue_date', 'total_net_value', 'supplier']
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

fetch("2017-02-15-receipts-texts.xz", "../data")
texts = pd.read_csv('../data/2017-02-15-receipts-texts.xz', dtype={'text': np.str}, low_memory=False)
texts['text'] = texts.text.str.upper()
texts = texts[~texts.text.isnull()]

fetch("2016-12-06-reimbursements.xz", "../data")
reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz', low_memory=False)
reimbursements = reimbursements.query('(subquota_description == "Congressperson meal")')
data = texts.merge(reimbursements, on='document_id')
len(data)


# There are 56710 meal reimbursements that have OCRed text.
# 
# ## Meals for kids
# 
# Usually there'll be the word `KIDS` or `INFANTIL` present on the receipt says.

# In[2]:

len(data[data.text.str.contains('KIDS?|INFANTIL')])


# Based on a previous analysis and after some quick look at the data, I found that some of them had already subtracted those items from the total value of the reimbursement. One way to reduce some of the false positives is the search for the `total_net_value` amount within the text of the receipt. To make things easier, we focus on those that are under R$ 1.000,00

# In[3]:

r = data.query('total_net_value < 1000')
r = r[r.text.str.contains('KIDS?|INFANTIL')]

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

r = r[r.apply(receipt_matches_net_value, axis=1)]
print(len(r))
report(r)


# Out of those reimbursements, I found at least 2 that are really suspicious and I'll try to get them reported.
# 
# I'm not sure how this affects meals prior to 2015 and after 2016 since the dataset I put together only has information about 2015-2016 ones, but it can contribute a lot for bringing up some reimbursements up in the rank of suspicious ones.
