from concurrent import futures
import json
import argparse
import time
import random
import itertools
import numpy as np
import os.path
import sys
import pandas as pd
import shutil
import requests
import requests.exceptions
import re
import logging
import json
from datetime import datetime, timedelta

LOGGER_NAME = 'fetch_cnpj'
TEMP_DATASET_PATH = os.path.join('data', 'companies-partial.xz')
INFO_DATASET_PATH = os.path.join('data', '{0}-{1}-{2}-companies.xz')
global logger, cnpj_list, num_threads, proxies_list

# source files mapped for extract cnpj

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                       'table_config.json')) as json_file:
    json_config = json.load(json_file)

datasets_cols = json_config['cnpj_cpf']


def configure_logger(verbosity):
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(verbosity)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(verbosity)
    logger.addHandler(ch)
    return logger


def transform_and_translate_data(json_data):
    """
    Transform main activity, secondary activity and partners list in
    multi columns and translate column names.
    """

    try:
        data = pd.DataFrame(columns=['atividade_principal',
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
                                     'data_situacao_especial',
                                     'qsa'])

        data = data.append(json_data, ignore_index=True)
    except Exception as e:
        logger.error("Error trying to transform and translate data:")
        logger.error(json_data)
        raise e

    def decompose_main_activity(value):
        struct = value
        if struct:
            return pd.Series(struct[0]). \
                rename_axis({'code': 'main_activity_code',
                             'text': 'main_activity'})
        else:
            return pd.Series({}, index=['main_activity_code', 'main_activity'])

    def decompose_secondary_activities(value):
        struct = value
        if struct and struct[0].get('text') != 'Não informada':
            new_attributes = [pd.Series(activity).
                              rename_axis({'code': 'secondary_activity_%i_code' % (index + 1),
                                           'text': 'secondary_activity_%i' % (index + 1)})
                              for index, activity in enumerate(struct)]
            return pd.concat(new_attributes)
        else:
            return pd.Series()

    def decompose_partners_list(value):
        struct = value
        if struct and len(struct) > 0:
            new_attributes = [pd.Series(partner).
                              rename_axis({
                                  'nome_rep_legal': 'partner_%i_legal_representative_name' % (index + 1),
                                  'qual_rep_legal': 'partner_%i_legal_representative_qualification' % (index + 1),
                                  'pais_origem': 'partner_%i_contry_origin' % (index + 1),
                                  'nome': 'partner_%i_name' % (index + 1),
                                  'qual': 'partner_%i_qualification' % (index + 1)})
                              for index, partner in enumerate(struct)]
            return pd.concat(new_attributes)
        else:
            return pd.Series()

    data = data.rename(columns={
        'abertura': 'opening',
        'atividade_principal': 'main_activity',
        'atividades_secundarias': 'secondary_activities',
        'bairro': 'neighborhood',
        'cep': 'zip_code',
        'complemento': 'additional_address_details',
        'data_situacao_especial': 'special_situation_date',
        'data_situacao': 'situation_date',
        'efr': 'responsible_federative_entity',
        'fantasia': 'trade_name',
        'logradouro': 'address',
        'motivo_situacao': 'situation_reason',
        'municipio': 'city',
        'natureza_juridica': 'legal_entity',
        'nome': 'name',
        'numero': 'number',
        'situacao_especial': 'special_situation',
        'situacao': 'situation',
        'telefone': 'phone',
        'tipo': 'type',
        'uf': 'state',
        'ultima_atualizacao': 'last_updated',
    })
    data['main_activity'] = data['main_activity'].fillna('{}')
    data['secondary_activities'] = data['secondary_activities'].fillna('{}')
    data['qsa'] = data['qsa'].fillna('{}')
    data = pd.concat([
        data.drop(['main_activity', 'secondary_activities', 'qsa'], axis=1),
        data['main_activity'].apply(decompose_main_activity),
        data['secondary_activities'].apply(decompose_secondary_activities),
        data['qsa'].apply(decompose_partners_list)],
        axis=1)
    return data


def load_temp_dataset():
    if os.path.exists(TEMP_DATASET_PATH):
        return pd.read_csv(TEMP_DATASET_PATH, low_memory=False)
    else:
        return pd.DataFrame(columns=['cnpj'])


def read_cnpj_source_files(cnpj_source_files):
    """
    Read the files passed as arguments and extract CNPJs from them.
    The file needs to be mapped in datasets_cols.
    """

    def extract_file_name_from_args(filepath):
        date = re.compile('\d+-\d+-\d+-').findall(os.path.basename(filepath))
        if date:
            filename_without_date = os.path.basename(
                filepath).replace(date[0], '')
        else:
            filename_without_date = os.path.basename(filepath)
        return filename_without_date[:filename_without_date.rfind('.')]

    def read_cnpj_list_to_import(filename, column):
        cnpj_list = pd.read_csv(filename,
                                usecols=([column]),
                                dtype={column: np.str}
                                )[column]
        cnpj_list = cnpj_list.map(lambda cnpj:
                                  str(cnpj).replace(r'[./-]', '')).where(cnpj_list.str.len() == 14).unique()
        return list(cnpj_list)

    filesNotFound = list(filter(lambda file: not os.path.exists(file) or
                                datasets_cols.get(
                                    extract_file_name_from_args(file.lower())) is None,
                                cnpj_source_files))
    filesFound = list(filter(lambda file: os.path.exists(file) and
                             datasets_cols.get(
                                 extract_file_name_from_args(file.lower())),
                             cnpj_source_files))
    cnpj_list_to_import = list(itertools.chain.from_iterable(
        map(lambda file: read_cnpj_list_to_import(file, datasets_cols.get(extract_file_name_from_args(file.lower()))),
            filesFound)))

    return cnpj_list_to_import, filesFound, filesNotFound


def remaining_cnpjs(cnpj_list_to_import, temp_dataset):
    cnpj_list = set(cnpj_list_to_import)
    already_fetched = set(temp_dataset['cnpj'].str.replace(r'[./-]', ''))
    return list(cnpj_list - already_fetched)


def fetch_cnpj_info(cnpj, timeout=60):
    url = 'http://receitaws.com.br/v1/cnpj/%s' % cnpj
    try:
        result = requests.get(url,
                              timeout=timeout,
                              proxies={'http': random.choice(proxies_list + [None])})
        if result.status_code == 200:
            cnpj_list.remove(cnpj)
            json_return = json.loads(result.text.replace(
                '\n', '').replace('\r', '').replace(';', ''))
            return json_return
        elif result.status_code == 429:
            logger.debug('Sleeping 60 seconds to try again.')
            logger.debug(result.text)
            time.sleep(60)
            logger.debug('Thread starting fetch again. {} CNPJs remaining.'.format(
                len(cnpj_list)))
        else:
            logger.debug(result.text)
    except requests.exceptions.Timeout as e:
        logger.debug(e)
    except requests.exceptions.ConnectionError as e:
        logger.debug(e)


parser = argparse.ArgumentParser(epilog="ex: python fetch_cnpj_info.py \
    ./data/2016-12-10-reimbursements.xz 2016-12-14-amendments.xz \
    -p 177.67.84.135:8080 177.67.82.80:8080 -t 10")
parser.add_argument('-v', '--verbosity', default='INFO',
                    help='level of logging messages.')
parser.add_argument('-t', '--threads', type=int, default=10,
                    help='number of threads to use in fetch process')
parser.add_argument('-p', '--proxies', nargs='*',
                    help='proxies list to distribuite requests in fetch process')
parser.add_argument('args', nargs='+',
                    help='source files from where to get CNPJs to fetch')
args = parser.parse_args()

if args.args:
    logger = configure_logger(args.verbosity)
    if args.proxies:
        proxies_list = ['http://' + proxy for proxy in args.proxies]
    else:
        proxies_list = []
    num_threads = args.threads
    cnpj_list_to_import, filesFound, filesNotFound = read_cnpj_source_files(
        args.args)
    temp_dataset = load_temp_dataset()
    cnpj_list = remaining_cnpjs(cnpj_list_to_import, temp_dataset)

    print('%i CNPJ\'s to be fetched' % len(cnpj_list))
    print('Starting fetch. {0} worker threads and {1} http proxies'.format(
        num_threads, len(proxies_list)))

    # Try again in case of error during fetch_cnpj_info
    while len(cnpj_list) > 0:
        with futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_cnpj_info = dict((executor.submit(fetch_cnpj_info, cnpj), cnpj)
                                       for cnpj in cnpj_list)
            last_saving_point = 0
            for future in futures.as_completed(future_to_cnpj_info):
                cnpj = future_to_cnpj_info[future]
                if future.exception() is None and future.result() is not None and future.result()['status'] == 'OK':
                    result_translated = transform_and_translate_data(
                        future.result())
                    temp_dataset = pd.concat([temp_dataset, result_translated])
                    if last_saving_point < divmod(len(temp_dataset.index), 100)[0]:
                        last_saving_point = divmod(len(temp_dataset.index), 100)[0]
                        print('###################################')
                        print('Saving information already fetched. {0} records'.format(
                            len(temp_dataset.index)))
                        temp_dataset.to_csv(TEMP_DATASET_PATH,
                                            compression='xz',
                                            encoding='utf-8',
                                            index=False)

    temp_dataset.to_csv(TEMP_DATASET_PATH,
                        compression='xz',
                        encoding='utf-8',
                        index=False)
    os.rename(TEMP_DATASET_PATH, INFO_DATASET_PATH.format(
        datetime.today().strftime("%Y"),
        datetime.today().strftime("%m"),
        datetime.today().strftime("%d")))

    if len(filesNotFound) > 0:
        print('The following files were not found:')
        for file in filesNotFound:
            print(file)
        print('Maybe they were misspelled or the CNPJ\'s columns are not mapped:')
        for file in datasets_cols:
            print('File: %s | Column: %s' % (file, datasets_cols[file]))

    print('%i CNPJ\'s listed in file(s)' % len(set(cnpj_list_to_import)))
    cnpj_list = remaining_cnpjs(cnpj_list_to_import, temp_dataset)
    print('%i CNPJ\'s remaining' % len(cnpj_list))
else:
    print('no files to fetch CNPJ\'s')
    print('type python fetch_cnpj_info.py -h for help')
