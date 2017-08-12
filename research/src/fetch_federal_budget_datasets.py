import time
import os
import zipfile
import pandas as pd
from urllib.request import urlretrieve


def download_datasets():

    filenames = map(lambda url: url.split('/')[-1], datasets_urls)

    for url, filename, dataset_name, translate_dataset in zip(datasets_urls, filenames, datasets_names, translation_functions):
        dataset_name = (time.strftime("%Y-%m-%d") + '-' + dataset_name)
        filepath = BASE_DATA_DIR + filename
        print('Downloading %s' % filename)
        urlretrieve(url, filepath)
        zip_ref = zipfile.ZipFile(filepath, 'r')
        zip_ref.extractall(BASE_DATA_DIR)
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

    data.to_csv(path_or_buf= BASE_DATA_DIR + dataset_name, sep=',',
                compression='xz', encoding='utf-8', index=False)


def translate_agreements_dataset(filepath, dataset_name):
    print('Renaming columns in: %s' % filepath.replace('.zip', ''))
    data = pd.read_csv(filepath_or_buffer=filepath.replace('.zip', ''), sep=';', decimal=',')
    data.rename(columns={
        'NR_CONVENIO': 'agreement_number',
        'ID_PROPOSTA': 'proposal_id',
        'DIA': 'day_signed',
        'MES': 'month_signed',
        'ANO': 'year_signed',
        'DIA_ASSIN_CONV': 'date_signed',
        'SIT_CONVENIO': 'situation',
        'SUBSITUACAO_CONV': 'subsituation',
        'SITUACAO_PUBLICACAO': 'publication_situation',
        'INSTRUMENTO_ATIVO': 'active',
        'IND_OPERA_OBTV': 'obtv_indicative',
        'NR_PROCESSO': 'process_number',
        'DIA_PUBL_CONV': 'published_date',
        'DIA_INIC_VIGENC_CONV': 'agreement_start_date',
        'DIA_FIM_VIGENC_CONV': 'agreement_end_date',
        'DIAS_PREST_CONTAS': 'accountability_date',
        'DIA_LIMITE_PREST_CONTAS': 'accountability_deadline',
        'QTDE_CONVENIOS': 'quantity_instrument_signeds',
        'QTD_TA': 'additives_quantity',
        'QTD_PRORROGA': 'legal_extensions',
        'VL_GLOBAL_CONV': 'total_value',
        'VL_REPASSE_CONV': 'federeal_government_contribution',
        'VL_CONTRAPARTIDA_CONV': 'counterparty_value',
        'VL_EMPENHADO_CONV': 'value_commited',
        'VL_DESEMBOLSADO_CONV': 'value_disbursed',
        'VL_SALDO_REMAN_TESOURO': 'returned_value_at_end',
        'VL_SALDO_REMAN_CONVENENTE': 'returned_value_to_convenient_at_end',
        'VL_INGRESSO_CONTRAPARTIDA': 'counterparty_value',
    }, inplace=True)

    data.to_csv(path_or_buf= BASE_DATA_DIR + dataset_name, sep=',',
                compression='xz', encoding='utf-8', index=False)


def dummy_translation_dataset(filepath, dataset_name):
    print('There is not translation function for %s' % filepath)
    data = pd.read_csv(filepath_or_buffer=filepath.replace('.zip', ''), sep=';', decimal=',', low_memory=False)
    data.to_csv(path_or_buf= BASE_DATA_DIR + dataset_name, sep=',',
                compression='xz', encoding='utf-8', index=False)

BASE_DATA_DIR = './data/'

datasets_urls = [
    'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_emenda.csv.zip',
    'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_convenio.csv.zip']#,
    # 'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_pagamento.csv.zip',
    # 'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_convenente.csv.zip']

datasets_names = [
    'amendments.xz',
    'agreements.xz']#,
    # 'payments.xz']

translation_functions = [
    translate_amendments_dataset,
    translate_agreements_dataset]#,
    # dummy_translation_dataset]

download_datasets()
