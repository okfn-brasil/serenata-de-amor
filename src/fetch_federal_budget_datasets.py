import time
import os
import zipfile
import pandas as pd
import numpy as np
from urllib.request import urlretrieve


def download_datasets():

    filenames = map(lambda url: url.split('/')[-1], datasets_urls)

    for url, filename, dataset_name, translate_dataset in zip(datasets_urls, filenames, datasets_names, translation_functions):
        dataset_name = (time.strftime("%Y-%m-%d") + '-' + dataset_name)
        filepath = 'data/%s' % filename
        print('Downloading %s' % filename)
        urlretrieve(url, filepath)
        zip_ref = zipfile.ZipFile(filepath, 'r')
        zip_ref.extractall('data')
        zip_ref.close()

        translate_dataset(filepath, dataset_name)

        print('Removing temporary files')
        os.remove(filepath)
        os.remove(filepath.replace('.zip', ''))


def translate_amendments_dataset(filepath, dataset_name):
    print('Renaming columns in: %s' % filepath.replace('.zip', ''))
    data = pd.read_csv(filepath_or_buffer=filepath.replace('.zip', ''), sep=';', decimal=',')
    data.rename(columns={
            'ID_PROPOSTA': 'proposal_id',
            'QUALIF_PROPONENTE': 'proponent_qualification',
            'COD_PROGRAMA_EMENDA': 'amendment_program_code',
            'NR_EMENDA': 'amendment_number',
            'NOME_PARLAMENTAR': 'congressperson_name',
            'BENEFICIARIO_EMENDA': 'amendment_beneficiary',
            'IND_IMPOSITIVO': 'tax_indicative',
            'TIPO_PARLAMENTAR': 'congressperson_type',
            'VALOR_REPASSE_PROPOSTA_EMENDA': 'amendment_proposal_tranfer_value',
            'VALOR_REPASSE_EMENDA': 'amendment_tranfer_value',
        }, inplace=True)

    # need to be done in another place else than translate
    data['amendment_beneficiary'] = data['amendment_beneficiary'].map(lambda x: str(x).zfill(14))

    data['congressperson_type'] = data['congressperson_type'].astype('category')
    data['congressperson_type'].cat.rename_categories([
            'seat',
            'committee',
            'individual',
        ], inplace=True)

    data['proponent_qualification'] = data['proponent_qualification'].astype('category')
    data['proponent_qualification'].cat.rename_categories([
            'parliamentary amendment beneficiary',
        ], inplace=True)

    data['tax_indicative'] = data['tax_indicative'].astype('category')
    data['tax_indicative'].cat.rename_categories([
            'no',
            'yes'
        ], inplace=True)

    data.to_csv(path_or_buf='data/%s' % dataset_name, sep=',',
                compression='xz', encoding='utf-8', index=False)


def dummy_translation_dataset(filepath, dataset_name):
    print('There is not translation function for %s' % filepath)
    data = pd.read_csv(filepath_or_buffer=filepath.replace('.zip', ''), sep=';', decimal=',', low_memory=False)
    data.to_csv(path_or_buf='data/%s' % dataset_name, sep=',',
                compression='xz', encoding='utf-8', index=False)


datasets_urls = [
    'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_emenda.csv.zip',
    'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_convenio.csv.zip',
    'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_pagamento.csv.zip']#,
    # 'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_convenente.csv.zip']

datasets_names = [
    'amendments.xz',
    'agreements.xz',
    'payments.xz']

translation_functions = [
    translate_amendments_dataset,
    dummy_translation_dataset,
    dummy_translation_dataset]

download_datasets()
