from concurrent import futures
import json
import numpy as np
import os.path
import pandas as pd
import pickle
import shutil
from urllib.error import HTTPError
from urllib.request import urlopen

INFO_DATASET_PATH = 'data/cnpj_info.xz'
TEMP_PATH = 'data/cnpj_info'

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

def read_csv(name):
    return pd.read_csv('data/2016-08-08-%s.xz' % name,
                       parse_dates=[16],
                       dtype={'document_id': np.str,
                              'congressperson_id': np.str,
                              'congressperson_document': np.str,
                              'term_id': np.str,
                              'cnpj_cpf': np.str,
                              'reimbursement_number': np.str})

def remaining_cnpjs(info_dataset):
    datasets = [read_csv(name)
                for name in ['current-year', 'last-year', 'previous-years']]
    dataset = pd.concat(datasets)
    del(datasets)
    is_cnpj = dataset['cnpj_cpf'].str.len() == 14.
    cnpj_list = set(dataset.loc[is_cnpj, 'cnpj_cpf'])
    already_fetched = set(info_dataset['cnpj'].str.replace(r'[./-]', ''))
    return list(cnpj_list - already_fetched)

def fetch_cnpj_info(cnpj, timeout=5):
    url = 'http://receitaws.com.br/v1/cnpj/%s' % cnpj
    print('Fetching %s' % cnpj)
    json_contents = urlopen(url, timeout=timeout).read().decode('utf-8')
    return json.loads(json_contents)

def write_cnpj_info(cnpj, cnpj_info):
    print('Writing %s' % cnpj)
    with open('%s/%s.pkl' % (TEMP_PATH, cnpj), 'wb') as f:
        pickle.dump(cnpj_info, f, pickle.HIGHEST_PROTOCOL)

def read_cnpj_info(cnpj_filename):
    with open('%s/%s' % (TEMP_PATH, cnpj_filename), 'rb') as f:
        return pickle.load(f)

def import_cnpj_infos(info_dataset):
    cnpjs_to_import = [filename
                       for filename in os.listdir(TEMP_PATH)
                       if filename.endswith('.pkl')]
    for filename in cnpjs_to_import:
        print('Importing %s' % filename)
        attributes = read_cnpj_info(filename)
        info_dataset = info_dataset.append(attributes, ignore_index=True)
    info_dataset.to_csv(INFO_DATASET_PATH,
                        compression='xz',
                        encoding='utf-8',
                        index=False)



if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)

info_dataset = load_info_dataset()
cnpj_list = remaining_cnpjs(info_dataset)
print('%i CNPJ\'s to be fetched' % len(cnpj_list))

with futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_cnpj_info = dict((executor.submit(fetch_cnpj_info, cnpj), cnpj)
                               for cnpj in cnpj_list)

    for future in futures.as_completed(future_to_cnpj_info):
        cnpj = future_to_cnpj_info[future]
        if future.exception() is not None:
            print('%r raised an exception: %s' % (cnpj, future.exception()))
        else:
            write_cnpj_info(cnpj, future.result())

import_cnpj_infos(info_dataset)

shutil.rmtree(TEMP_PATH)
