import json
from optparse import OptionParser
import time
import random
import itertools
import numpy as np
import os.path
import pandas as pd
import pickle
import shutil
import requests
import requests.exceptions
import re

INFO_DATASET_PATH = os.path.join('data', 'cnpj-info.xz')

datasets_cols = {'reimbursements': 'cnpj_cpf',
                 'current-year': 'cnpj_cpf',
                 'last-year': 'cnpj_cpf',
                 'previous-years': 'cnpj_cpf',
                 'amendments': 'amendment_beneficiary'}

def load_info_dataset():
    if os.path.exists(INFO_DATASET_PATH):
        return pd.read_csv(INFO_DATASET_PATH)
    else:
        return pd.DataFrame(columns=['atividade_principal',
                                     'data_situacao',
                                     'tipo',
                                     'nome',
                                     'telefone',
                                     'atividades_secundarias',
                                     'situacao',
                                     'bairro',
                                     'logradouro',
                                     'numero',
                                     'cep',
                                     'municipio',
                                     'uf',
                                     'abertura',
                                     'natureza_juridica',
                                     'fantasia',
                                     'cnpj',
                                     'ultima_atualizacao',
                                     'status',
                                     'complemento',
                                     'email',
                                     'efr',
                                     'motivo_situacao',
                                     'situacao_especial',
                                     'data_situacao_especial'])


def read_cnpj_list_to_import(filename, column):
    cnpj_list = pd.read_csv(filename,
                    usecols=([column]),
                    dtype={column: np.str}
                )[column]
    cnpj_list = cnpj_list.map(lambda cnpj:
                              str(cnpj).replace(r'[./-]', '')).where(cnpj_list.str.len() == 14).unique()
    return list(cnpj_list)


def remaining_cnpjs(cnpj_list_to_import, info_dataset):
    cnpj_list = set(cnpj_list_to_import)
    already_fetched = set(info_dataset['cnpj'].str.replace(r'[./-]', ''))
    return list(cnpj_list - already_fetched)


def fetch_cnpj_info(cnpj, timeout=50):
    candidate_proxies = ['http://191.101.153.227:8080',
                         'http://144.76.238.105:80',
                         'http://77.174.87.85:80',
                         'http://138.68.239.154:3128',
                         'http://84.196.169.161:80',
                         'http://181.215.238.132:8080',
                         None]
    url = 'http://receitaws.com.br/v1/cnpj/%s' % cnpj
    print('Fetching %s' % cnpj)
    try:
        result = requests.get(url,
                              timeout=timeout,
                            #   proxies={'http': random.choice(candidate_proxies)}
                              )
        if result.status_code == 200:
            return result.json()
        elif result.status_code == 429:
            print(result.text)
            print('Sleeping 60 seconds to try again.')
            time.sleep(60)
        else:
            print(result.text)
    except requests.exceptions.Timeout as e:
        print(e)
    except requests.exceptions.ConnectionError as e:
        print(e)


def extract_dataset_name(filepath):
    date = re.compile('\d+-\d+-\d+-').findall(os.path.basename(filepath))
    if date:
        filename_without_date = os.path.basename(filepath).replace(date[0], '')
    else:
        filename_without_date = os.path.basename(filepath)
    return filename_without_date[:filename_without_date.rfind('.')]


parser = OptionParser()
(options, args) = parser.parse_args()

if args:
    filesNotFound = list(filter(lambda file: not os.path.exists(file) or
                                             datasets_cols.get(extract_dataset_name(file.lower())) is None, args))
    filesFound = list(filter(lambda file: os.path.exists(file) and
                                          datasets_cols.get(extract_dataset_name(file.lower())), args))
    cnpj_list_to_import = list(itertools.chain.from_iterable(
            map(lambda file: read_cnpj_list_to_import(file,
                                                      datasets_cols.get(extract_dataset_name(file.lower()))),
                filesFound)))
    info_dataset = load_info_dataset()
    cnpj_list = remaining_cnpjs(cnpj_list_to_import, info_dataset)

    print('%i CNPJ\'s to be fetched' % len(cnpj_list_to_import))

    for cnpj in cnpj_list:
        result = fetch_cnpj_info(cnpj)
        if result != None and result['status'] == 'OK':
            info_dataset = info_dataset.append(result, ignore_index=True)

    info_dataset.to_csv(INFO_DATASET_PATH,
                        compression='xz',
                        encoding='utf-8',
                        index=False)

    if len(filesNotFound) > 0:
        print('The following files were not found:')
        for file in filesNotFound:
            print(file)
        print('Maybe they were misspelled or the CNPJ\'s columns are not mapped:')
        for file in datasets_cols:
            print('File: %s | Column: %s' % (file, datasets_cols[file]))

    print('%i CNPJ\'s listed in file' % len(set(cnpj_list_to_import)))
    cnpj_list = remaining_cnpjs(cnpj_list_to_import, info_dataset)
    print('%i CNPJ\'s remaining' % len(cnpj_list))
else:
    print('no files to fetch CNPJ\'s')
    print('usage: fetch_cnpj_info.py \'filename\'')
    print('ex: fetch_cnpj_info.py \'./data/2016-12-10-reimbursements.xz 2016-12-14-amendments.xz\' ')
