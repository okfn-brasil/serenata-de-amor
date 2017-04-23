
# coding: utf-8

# # Um mês depois do primeiro mutirão
# 
# https://datasciencebr.com/um-m%C3%AAs-depois-do-primeiro-mutir%C3%A3o-369975af4bb5

# In[1]:

import numpy as np
import pandas as pd
from serenata_toolbox.datasets import fetch

fetch('2016-12-06-reimbursements.xz', '../data')
reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz',
                             dtype={'document_number': np.str, 'year': np.str},
                             low_memory=False)


# In[2]:

import os.path
import urllib.request
import zipfile

inbox_url = 'https://github.com/datasciencebr/serenata-de-amor-inbox/archive/master.zip'
inbox_filepath = '/tmp/master.zip'
if not os.path.exists(inbox_filepath):
    urllib.request.urlretrieve(inbox_url, inbox_filepath)

if not os.path.exists('/tmp/serenata-de-amor-inbox'):
    zip_ref = zipfile.ZipFile(inbox_filepath, 'r')
    zip_ref.extractall('/tmp')
    zip_ref.close()


# In[3]:

emails = sc.wholeTextFiles('/tmp/serenata-de-amor-inbox-master/Pedido de Acesso a Informacao/**/message.txt')
emails.count()


# In[4]:

import os
import re

emails = sc.wholeTextFiles('/tmp/serenata-de-amor-inbox-master/Resposta da Camara/**/message.txt')
emails = emails.filter(lambda txt: 'Discussion Thread' in txt[1])
messages = emails     .map(lambda txt: txt[1].split('\n--------------'))     .map(lambda txt: next(x for x in txt if 'Resposta By E-mail' in x))     .map(lambda txt: re.sub(r'(?:\-){2,}', '', txt))
print(messages.count())


# In[5]:

emails_with_return = messages     .filter(lambda txt: 'devolução' in txt)
emails_lines_with_return = emails_with_return     .map(lambda txt: txt.split('\n'))     .cache()
    
regex = r'R\$ ((?:\d+)(?:,\d+)?)'

def get_report_id(line):
    return re.search(r'Question Reference.+(\d{6}\-\d{6})', line).groups()[0]

def returned_amount(string):
    match = re.search(regex, string)
    value = match.group(1) if match else ''
    return float(value.replace(',', '.'))


report_ids_with_return = emails_lines_with_return     .map(lambda lines: [line for line in lines if 'Question Reference' in line])     .map(lambda lines: get_report_id(lines[0]))     .collect()

values = emails_lines_with_return     .map(lambda txt: next(x for x in txt if 'devolução' in x))     .map(returned_amount)
values.count(), values.sum()


# In[6]:

returned_values = pd.DataFrame([
    pd.Series(report_ids_with_return, name='report_id'),
    pd.Series(values.collect(), name='returned_value'),
]).T


# In[7]:

def get_document_number(line):
    return re.search(r'numAno=(\d{4}).+idDocumento=(\d+)', line).groups()[0:2]

def get_investigator(line):
    return re.search(r'\((.+)\) \(', line).groups()[0]

email_lines = messages     .map(lambda txt: txt.split('\n'))     .cache()

document_numbers = email_lines     .map(lambda lines: [line for line in lines if 'idDocumento=' in line])     .map(lambda lines: [get_document_number(line) for line in lines])     .collect()

report_ids = email_lines     .map(lambda lines: [line for line in lines if 'Question Reference' in line])     .map(lambda lines: get_report_id(lines[0]))     .collect()

import itertools

reports = pd.DataFrame([
    pd.Series(document_numbers, name='document'),
    pd.Series(report_ids, name='report_id'),
]).T
documents = list(itertools.chain(*reports['document'].values))
report_docs = pd.DataFrame(documents,
                           columns=('year', 'document_number'))
report_docs = pd.merge(report_docs,
                       reimbursements,
                       how='left')

def matching_id(values):
    does_match = (report_docs['year'] == values[0]) &         (report_docs['document_number'] == values[1])
    return report_docs.loc[does_match, 'document_id'].iloc[0]

reports = pd.merge(reports, returned_values, how='left')
reports['document_id'] = reports['document']     .apply(lambda row: [matching_id(x) for x in row])

new_reports = reports     .apply(lambda x: pd.Series(x['document_id']), axis=1)     .stack()     .reset_index(level=1, drop=True)
new_reports.name = 'document_id'
new_reports = reports.drop('document_id', axis=1).join(new_reports)
new_reports.drop('document', axis=1, inplace=True)
new_reports['document_id'] = new_reports['document_id'].astype(np.int)

dataset = pd.merge(new_reports, reimbursements)
dataset.rename(columns={'congressperson_name': 'Parlamentar'}, inplace=True)

def aggregation(row):
    return pd.Series({
            'Respostas': len(row),
            'UF': row['state'].values[0],
            'Devolvido': row['returned_value'].sum(),
            'Devoluções': row['returned_value'].notnull().sum(),
        })

keys = ['UF',
        'Parlamentar',
        'Respostas',
        'Devoluções',
        'Devolvido']
answers_dataset = dataset.groupby('Parlamentar')     .apply(aggregation)     .fillna(0)     .reset_index()[keys]

def number_to_currency(number):
    return 'R$ {:.2f}'.format(number).replace('.', ',')

def dataframe_to_string(df):
    print(df.to_string(index=False, float_format=number_to_currency))


answers_docs = dataset['document_id']
dataframe_to_string(answers_dataset[answers_dataset['Devolvido'] > 0])


# In[8]:

emails_wo_return = messages.subtract(emails_with_return)
emails_wo_return.count()


# In[9]:

import configparser
settings = configparser.RawConfigParser()
settings.read('../config.ini')
api_key = settings.get('Google', 'APIKey')
api_url = 'https://www.googleapis.com/urlshortener/v1/url?key={}'.format(api_key)

def source_url(mailpath):
    return 'https://github.com/datasciencebr/serenata-de-amor-inbox/tree/39dbf4392359acb3e437287c0884b7daf50fcc59/Resposta%20da%20Camara/{}'.format(mailpath)

def shorten_url(url):
    import json
    import requests
    data = json.dumps({'longUrl': url})
    result = requests.post(api_url,
                           headers={'content-type': 'application/json'},
                           data=data)
    return result.json()['id']

emails_wo_return = emails     .filter(lambda txt: 'devolução' not in txt[1])     .cache()
    
urls = emails_wo_return     .map(lambda txt: txt[0].split('/')[-2])     .map(source_url)     .map(shorten_url)     .collect()

document_numbers = emails_wo_return     .map(lambda txt: txt[1].split('\n'))     .map(lambda lines: [line for line in lines if 'idDocumento=' in line])     .map(lambda lines: [get_document_number(line) for line in lines])     .collect()

reports = pd.DataFrame([
    pd.Series(urls, name='Resposta Oficial'),
    pd.Series(document_numbers, name='document'),
]).T
reports['year'] = reports['document'].apply(lambda x: x[0][0]).values
reports['document_number'] = reports['document'].apply(lambda x: x[0][1]).values

reports = pd.merge(reports, reimbursements, how='left')
reports = reports     .drop('document', 1)     .rename(columns={'congressperson_name': 'Parlamentar'})     .sort_values('Parlamentar')

pd.set_option('display.max_colwidth', -1)
keys = ['Resposta Oficial',
        'Parlamentar']
reports.index = range(len(reports.index))
dataframe_to_string(reports[keys])


# In[10]:

import json

fetch('2017-02-14-reports.csv', '../data')
reports = pd.read_csv('../data/2017-02-14-reports.csv')
reports = reports.query('report_id.notnull()')
reports['documents'] = reports['documents'].apply(json.loads)
reported_docs = reports.loc[reports['report_id'].str.startswith('17'),
                            'documents'].values
reported_docs = list(itertools.chain(*reported_docs))
waiting_answer_docs = list(set(reported_docs) - set(answers_docs))
reports = reimbursements     .loc[reimbursements['document_id'].isin(waiting_answer_docs),
         ['state', 'congressperson_name']]
reports = reports     .drop_duplicates('congressperson_name')     .sort_values('congressperson_name')     .rename(columns={'congressperson_name': 'Parlamentar',
                     'state': 'UF'})
reports.index = range(len(reports.index))
pd.set_option('display.max_rows', 1000000)
dataframe_to_string(reports)


# In[ ]:



