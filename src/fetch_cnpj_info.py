from concurrent import futures
import json
import argparse
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
global cnpj_list, num_threads, proxies_list

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
    url = 'http://receitaws.com.br/v1/cnpj/%s' % cnpj

    try:
        result = requests.get(url,
                              timeout=timeout,
                              proxies={'http': random.choice(proxies_list + [None])})
        if result.status_code == 200:
            cnpj_list.remove(cnpj)
            return result.json()
        elif result.status_code == 429:
            print(result.text)
            print('Sleeping 60 seconds to try again.')
            time.sleep(60)
            print('Thread starting fetch again. {} CNPJs remaining.'.format(len(cnpj_list)))
        else:
            print(result.text)
    except requests.exceptions.Timeout as e:
        print(e)
    except requests.exceptions.ConnectionError as e:
        print(e)


def extract_file_name_from_args(filepath):
    date = re.compile('\d+-\d+-\d+-').findall(os.path.basename(filepath))
    if date:
        filename_without_date = os.path.basename(filepath).replace(date[0], '')
    else:
        filename_without_date = os.path.basename(filepath)
    return filename_without_date[:filename_without_date.rfind('.')]


parser = argparse.ArgumentParser()
parser.add_argument('-t', '--threads',
                    type=int,
                    default=10,
                    help='number of threads to use in fetch process')
parser.add_argument('-p', '--proxies',
                    nargs='*',
                    help='proxies list to distribuite requests in fetch process')
parser.add_argument('args',
                    nargs='+',
                    help='source files from where to get CNPJs to fetch')
args = parser.parse_args()

if args.args:
    num_threads = args.threads
    proxies_list = ['http://' + proxy for proxy in args.proxies]
    filesNotFound = list(filter(lambda file: not os.path.exists(file) or
                                             datasets_cols.get(extract_file_name_from_args(file.lower())) is None, args.args))
    filesFound = list(filter(lambda file: os.path.exists(file) and
                                          datasets_cols.get(extract_file_name_from_args(file.lower())), args.args))
    cnpj_list_to_import = list(itertools.chain.from_iterable(
            map(lambda file: read_cnpj_list_to_import(file,
                                                      datasets_cols.get(extract_file_name_from_args(file.lower()))),
                filesFound)))
    info_dataset = load_info_dataset()
    cnpj_list = remaining_cnpjs(cnpj_list_to_import, info_dataset)

    print('%i CNPJ\'s to be fetched' % len(cnpj_list))
    print('starting fetch. {0} worker threads and {1} http proxies'.format(num_threads, len(proxies_list)))

    with futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_cnpj_info = dict((executor.submit(fetch_cnpj_info, cnpj), cnpj)
                                   for cnpj in cnpj_list)

        last_saving_point = 0
        for future in futures.as_completed(future_to_cnpj_info):
            cnpj = future_to_cnpj_info[future]
            if future.exception() is not None:
                print('%r raised an exception: %s' % (cnpj, future.exception()))
            elif future.result() is not None and future.result()['status'] == 'OK':
                info_dataset = info_dataset.append(future.result(), ignore_index=True)
                if last_saving_point < divmod(len(info_dataset.index), 100)[0]:
                    last_saving_point = divmod(len(info_dataset.index), 100)[0]
                    info_dataset.to_csv(INFO_DATASET_PATH,
                                        compression='xz',
                                        encoding='utf-8',
                                        index=False)

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

    print('%i CNPJ\'s listed in file(s)' % len(set(cnpj_list_to_import)))
    cnpj_list = remaining_cnpjs(cnpj_list_to_import, info_dataset)
    print('%i CNPJ\'s remaining' % len(cnpj_list))
else:
    print('no files to fetch CNPJ\'s')
    print('usage: fetch_cnpj_info.py \'filename\'')
    print('ex: fetch_cnpj_info.py \'./data/2016-12-10-reimbursements.xz 2016-12-14-amendments.xz\' -p 177.67.84.135:8080 177.67.82.80:8080 -t 10')
