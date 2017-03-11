from datetime import datetime, timedelta
import os
import zipfile
import pandas as pd
from urllib.request import urlretrieve


def download_datasets():

    def download(date, dataset):
        year = date.strftime("%Y")
        month = date.strftime("%m")
        day = date.strftime("%d")
        filename, headers = urlretrieve(BASE_URL + 'a={0}&m={1}&d={2}&consulta={3}'.format(year, month, day, dataset),
                                        BASE_DATA_DIR + '{0}.zip'.format(dataset))
        if 'text/html' not in headers['Content-Type']:
            print('Dataset {0} downloaded as of {1}-{2}-{3}'.format(dataset, year, month, day))
            return year, month, day
        else:
            # print('File not found for dataset {0} from date {1}'.format(dataset, datetime.today().strftime("%Y-%m-%d")))
            earlier = date - timedelta(days=1)
            return download(earlier, dataset)

    for dataset_name, translate_dataset in zip(datasets_names.keys(), translation_functions):
        year, month, day = download(datetime.today(), dataset_name)
        zip_ref = zipfile.ZipFile(BASE_DATA_DIR + dataset_name + '.zip', 'r')
        zip_ref.extractall(BASE_DATA_DIR)
        zip_ref.close()

        csv_file = '{0}{1}{2}{3}_{4}.csv'.format(BASE_DATA_DIR, year, month, day, dataset_name.upper())
        translate_dataset(csv_file, datasets_names.get(dataset_name), year, month, day)

        print('Removing temporary files')
        os.remove(csv_file)
        os.remove(BASE_DATA_DIR + dataset_name + '.zip')


def translate_inident_and_suspended_companies_dataset(filepath, dataset_name, year, month, day):
    print('Renaming columns in: %s' % filepath)
    data = pd.read_csv(filepath_or_buffer=filepath, sep='\t', encoding='latin')
    data.rename(columns={
                'Tipo de Pessoa': 'entity_type',
                'CPF ou CNPJ do Sancionado': 'sanctioned_cnpj_cpf',
                'Nome Informado pelo Órgão Sancionador': 'name_given_by_sanctioning_body',
                'Razão Social - Cadastro Receita': 'company_name_receita_database',
                'Nome Fantasia - Cadastro Receita': 'trading_name_receita_database',
                'Número do processo': 'process_number',
                'Tipo Sanção': 'sanction_type',
                'Data Início Sanção': 'sanction_start_date',
                'Data Final Sanção': 'sanction_end_date',
                'Órgão Sancionador': 'sanctioning_body',
                'UF Órgão Sancionador': 'state_of_sanctioning_body',
                'Origem Informações': 'data_source',
                'Data Origem Informações': 'data_source_date',
                'Data Publicação': 'published_date',
                'Publicação': 'publication',
                'Detalhamento': 'detailing',
        }, inplace=True)

    # data['entity_type'] = data['entity_type'].astype('category')
    # data['entity_type'].cat.rename_categories(['person', 'company'], inplace=True)

    # need to be done in another place else than translate
    # data['sanctioned_cnpj_cpf'] = data['sanctioned_cnpj_cpf'].map(lambda x: str(x).zfill(14))

    data.to_csv(path_or_buf='{0}{1}-{2}-{3}-{4}.xz'.format(BASE_DATA_DIR, year, month, day, dataset_name), sep=',',
                compression='xz', encoding='utf-8', index=False)


def translate_national_register_punished_companies_dataset(filepath, dataset_name, year, month, day):
    print('Renaming columns in: %s' % filepath)
    data = pd.read_csv(filepath_or_buffer=filepath, sep='\t', encoding='latin')
    data.rename(columns={
        'Tipo de Pessoa': 'entity_type',
        'CPF ou CNPJ do Sancionado': 'sanctioned_cnpj_cpf',
        'Nome Informado pelo Órgão Sancionador': 'name_given_by_sanctioning_body',
        'Razão Social - Cadastro Receita': 'company_name_receita_database',
        'Nome Fantasia - Cadastro Receita': 'trading_name_receita_database',
        'Número do processo': 'process_number',
        'Tipo Sanção': 'sanction_type',
        'Data Início Sanção': 'sanction_start_date',
        'Data Final Sanção': 'sanction_end_date',
        'Órgão Sancionador': 'sanctioning_body',
        'UF Órgão Sancionador': 'state_of_sanctioning_body',
        'Origem Informações': 'data_source',
        'Data Origem Informações': 'data_source_date',
        'Data Publicação': 'published_date',
        'Publicação': 'publication',
        'Detalhamento': 'detailing',
        'Valor da Multa': 'penality_value',
    }, inplace=True)

    # data['entity_type'] = data['entity_type'].astype('category')
    # data['entity_type'].cat.rename_categories(['person', 'company'], inplace=True)

    # need to be done in another place else than translate
    # data['company_cnpj'] = data['company_cnpj'].map(lambda x: str(x).zfill(14))

    data.to_csv(path_or_buf='{0}{1}-{2}-{3}-{4}.xz'.format(BASE_DATA_DIR, year, month, day, dataset_name), sep=',',
                compression='xz', encoding='utf-8', index=False)


def translate_impeded_non_profit_entities_dataset(filepath, dataset_name, year, month, day):
    print('Renaming columns in: %s' % filepath)
    data = pd.read_csv(filepath_or_buffer=filepath, sep='\t', encoding='latin')
    data.rename(columns={
        'CNPJ Entidade': 'company_cnpj',
        'Nome Entidade': 'compay_name',
        'Número Convênio': 'agreement_number',
        'Órgão Concedente': 'grating_body',
        'Motivo Impedimento': 'impediment_reason'
    }, inplace=True)

    # need to be done in another place else than translate
    data['company_cnpj'] = data['company_cnpj'].map(lambda x: str(x).zfill(14))

    data.to_csv(path_or_buf='{0}{1}-{2}-{3}-{4}.xz'.format(BASE_DATA_DIR, year, month, day, dataset_name), sep=',',
                compression='xz', encoding='utf-8', index=False)


def dummy_translation_dataset(filepath, dataset_name, year, month, day):
    print('There is not translation function for %s' % filepath)
    data = pd.read_csv(filepath_or_buffer=filepath, sep='\t', low_memory=False)
    data.to_csv(path_or_buf='{0}{1}-{2}-{3}-{4}.xz'.format(BASE_DATA_DIR, year, month, day, dataset_name), sep=',',
                compression='xz', encoding='utf-8', index=False)

BASE_URL = 'http://arquivos.portaldatransparencia.gov.br/downloads.asp?'
BASE_DATA_DIR = './data/'

datasets_names = {
    'ceis': 'inident-and-suspended-companies',
    'cnep': 'national-register-punished-companies',
    'cepim': 'impeded-non-profit-entities'}

translation_functions = [
    translate_inident_and_suspended_companies_dataset,
    translate_national_register_punished_companies_dataset,
    translate_impeded_non_profit_entities_dataset]

download_datasets()
