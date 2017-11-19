import os
import shutil
import time
import zipfile

import pandas as pd
import requests
from tqdm import tqdm


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')
DOWNLOAD_BOCK_SIZE = 2 ** 19  # ~ 500kB
READ_KWARGS = dict(
    low_memory=False,
    encoding="ISO-8859-1",
    sep=';'
)


def download(url, path, block_size=None):
    """Saves file from remote `url` into local `path` showing a progress bar"""
    block_size = block_size or DOWNLOAD_BOCK_SIZE
    request = requests.get(url, stream=True)
    total = int(request.headers.get('content-length', 0))
    with open(path, 'wb') as file_handler:
        kwargs = dict(total=total, unit='B', unit_scale=True)
        for data in tqdm(request.iter_content(block_size), **kwargs):
            file_handler.write(data)


def read_csv(path, chunksize=None):
    """Wrapper to read CSV with default args and an optional `chunksize`"""
    kwargs = READ_KWARGS.copy()
    if chunksize:
        kwargs['chunksize'] = 10000

    data = pd.read_csv(path, **kwargs)
    return pd.concat([chunk for chunk in data]) if chuncksize else data


def folder_walk(year):
    ret_dict = {}
    if year == '2010':
        donations_data_candidates = []
        donations_data_parties = []
        donations_data_committees = []
        for root, dirs, files in os.walk("prestacao_contas_2010", topdown=False):
            for name in files:
                if 'Receitas' in name:
                    data = read_csv(os.path.join(root, name))
                    if 'candidato' in os.path.join(root, name):
                        donations_data_candidates.append(data)
                    elif 'comite' in os.path.join(root, name):
                        donations_data_committees.append(data)
                    elif 'partido' in os.path.join(root, name):
                        donations_data_parties.append(data)

        donations_data_candidates = pd.concat(donations_data_candidates)
        donations_data_parties = pd.concat(donations_data_parties)
        donations_data_committees = pd.concat(donations_data_committees)
        shutil.rmtree('prestacao_contas_2010')
        ret_dict = {'candidates': donations_data_candidates,
                    'parties': donations_data_parties,
                    'committees': donations_data_committees}
    else:
        if year == '2012':
            path_candid = os.path.join('prestacao_final_2012',
                                       'receitas_candidatos_2012_brasil.txt')
            path_parties = os.path.join('prestacao_final_2012',
                                        'receitas_partidos_2012_brasil.txt')
            path_committ = os.path.join('prestacao_final_2012',
                                        'receitas_comites_2012_brasil.txt')
        elif year == '2014':
            path_candid = os.path.join('prestacao_final_2014',
                                       'receitas_candidatos_2014_brasil.txt')
            path_parties = os.path.join('prestacao_final_2014',
                                        'receitas_partidos_2014_brasil.txt')
            path_committ = os.path.join('prestacao_final_2014',
                                        'receitas_comites_2014_brasil.txt')
        elif year == '2016':
            path_candid = os.path.join('prestacao_contas_final_2016',
                                   ('receitas_candidatos_prestacao_contas_final_2016_brasil'  # noqa
                                    '.txt'))
            path_parties = os.path.join('prestacao_contas_final_2016',
                                        ('receitas_partidos_prestacao_contas_final_2016_brasil'  # noqa
                                         '.txt'))

        donations_data_candidates = read_csv(path_candid, 10000)
        ret_dict['candidates'] = donations_data_candidates

        donations_data_parties = read_csv(path_parties, 10000)
        ret_dict['parties'] = donations_data_parties

        if year != '2016':
            donations_data_committees = read_csv(path_committ, 10000)
            ret_dict['committees'] = donations_data_committees

        if year != '2016':
            shutil.rmtree('prestacao_final_' + year)
        else:
            shutil.rmtree('prestacao_contas_final_2016')

    return ret_dict


def correct_columns(donations_data):
    if 'candidates' in donations_data.keys():
        donations_data['candidates'].rename(columns={'Descricao da receita':
                                                     'Descrição da receita',
                                                     'Especie recurso':
                                                     'Espécie recurso',
                                                     'Numero candidato':
                                                     'Número candidato',
                                                     'Numero do documento':
                                                     'Número do documento',
                                                     'Numero Recibo Eleitoral':
                                                     'Número Recibo Eleitoral',
                                                     'Sigla  Partido':
                                                     'Sigla Partido'},
                                            inplace=True)
    if 'parties' in donations_data.keys():
        donations_data['parties'].rename(columns={'Sigla  Partido':
                                                  'Sigla Partido',
                                                  'Número recibo eleitoral':
                                                  'Número Recibo Eleitoral'},
                                         inplace=True)
    if 'committees' in donations_data.keys():
        donations_data['committees'].rename(columns={'Sigla  Partido':
                                                     'Sigla Partido',
                                                     'Tipo comite':
                                                     'Tipo Comite',
                                                     'Número recibo eleitoral':
                                                     'Número Recibo Eleitoral'},  # noqa
                                            inplace=True)


def translate_columns(donations_data):
    translations = {'Cargo': 'post',
                    'CNPJ Prestador Conta': 'accountable_company_id',
                    'Cod setor econômico do doador': 'donor_economic_setor_id',
                    'Cód. Eleição': 'election_id',
                    'CPF do candidato': 'candidate_cpf',
                    'CPF do vice/suplente': 'substitute_cpf',
                    'CPF/CNPJ do doador': 'donor_cnpj_or_cpf',
                    'CPF/CNPJ do doador originário':
                    'original_donor_cnpj_or_cpf',
                    'Data da receita': 'revenue_date',
                    'Data e hora': 'date_and_time',
                    'Desc. Eleição': 'election_description',
                    'Descrição da receita': 'revenue_description',
                    'Entrega em conjunto?': 'batch',
                    'Espécie recurso': 'type_of_revenue',
                    'Fonte recurso': 'source_of_revenue',
                    'Município': 'city',
                    'Nome candidato': 'candidate_name',
                    'Nome da UE': 'electoral_unit_name',
                    'Nome do doador': 'donor_name',
                    'Nome do doador (Receita Federal)':
                    'donor_name_for_federal_revenue',
                    'Nome do doador originário': 'original_donor_name',
                    'Nome do doador originário (Receita Federal)':
                    'original_donor_name_for_federal_revenue',
                    'Número candidato': 'candidate_number',
                    'Número candidato doador': 'donor_candidate_number',
                    'Número do documento': 'document_number',
                    'Número partido doador': 'donor_party_number',
                    'Número Recibo Eleitoral': 'electoral_receipt_number',
                    'Número UE': 'electoral_unit_number',
                    'Sequencial Candidato': 'candidate_sequence',
                    'Sequencial prestador conta': 'accountable_sequence',
                    'Sequencial comite': 'committee_sequence',
                    'Sequencial Diretorio': 'party_board_sequence',
                    'Setor econômico do doador': 'donor_economic_sector',
                    'Setor econômico do doador originário':
                    'original_donor_economic_sector',
                    'Sigla da UE': 'electoral_unit_abbreviation',
                    'Sigla Partido': 'party_acronym',
                    'Sigla UE doador': 'donor_electoral_unit_abbreviation',
                    'Tipo de documento': 'document_type',
                    'Tipo diretorio': 'party_board_type',
                    'Tipo doador originário': 'original_donor_type',
                    'Tipo partido': 'party_type',
                    'Tipo receita': 'revenue_type',
                    'Tipo comite': 'committee_type',
                    'UF': 'state',
                    'Valor receita': 'revenue_value'}
    if 'candidates' in donations_data.keys():
        donations_data['candidates'].rename(columns=translations,
                                            inplace=True)
    if 'parties' in donations_data.keys():
        donations_data['parties'].rename(columns=translations,
                                         inplace=True)
    if 'committees' in donations_data.keys():
        donations_data['committees'].rename(columns=translations,
                                            inplace=True)


def strip_columns_names(donations_data, key):
    if key in donations_data.keys():
        columns_candidates = donations_data[key].columns.values
        columns_mod_candidates = {}
        for name in columns_candidates:
            columns_mod_candidates[name] = name.strip()
        donations_data[key].rename(columns=columns_mod_candidates,
                                   inplace=True)


def download_base(url, year):
    file_name = url.split('/')[-1]
    print("Downloading " + file_name)
    download(url, file_name)
    print("Uncompressing downloaded data.")
    with zipfile.ZipFile(file_name, "r") as zip_ref:
        zip_ref.extractall(file_name.split('.')[0])
    os.remove(file_name)

    print("Reading all the data and creating the dataframes...")

    donations_data = folder_walk(year)

    strip_columns_names(donations_data, 'candidates')
    strip_columns_names(donations_data, 'parties')
    strip_columns_names(donations_data, 'committees')

    return donations_data


if __name__ == "__main__":
    base_url = ('http://agencia.tse.jus.br/estatistica/sead/odsele/'
                'prestacao_contas/')
    url = base_url + 'prestacao_contas_2010.zip'
    donations_data_2010 = download_base(url, '2010')
    url = base_url + 'prestacao_final_2012.zip'
    donations_data_2012 = download_base(url, '2012')
    url = base_url + 'prestacao_final_2014.zip'
    donations_data_2014 = download_base(url, '2014')
    url = base_url + 'prestacao_contas_final_2016.zip'
    donations_data_2016 = download_base(url, '2016')

    donations_data = [donations_data_2010, donations_data_2012,
                      donations_data_2014, donations_data_2016]

    donations_candidates_concatenated = []
    donations_parties_concatenated = []
    donations_committees_concatenated = []

    for data in donations_data:
        correct_columns(data)
        translate_columns(data)
        if 'candidates' in data.keys():
            donations_candidates_concatenated.append(data['candidates'])
        if 'parties' in data.keys():
            donations_parties_concatenated.append(data['parties'])
        if 'committees' in data.keys():
            donations_committees_concatenated.append(data['committees'])

    donations_candidates_concatenated = pd.concat(donations_candidates_concatenated)  # noqa
    donations_parties_concatenated = pd.concat(donations_parties_concatenated)
    donations_committees_concatenated = pd.concat(donations_committees_concatenated)  # noqa

    print("Saving dataframes in csv files (.xz)...")

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    donations_candidates_concatenated.to_csv(os.path.join(DATA_PATH,
                                             time.strftime("%Y-%m-%d") +
                                             '-donations_candidates.xz'),
                                             compression='xz')
    donations_parties_concatenated.to_csv(os.path.join(DATA_PATH,
                                          time.strftime("%Y-%m-%d") +
                                          '-donations_parties.xz'),
                                          compression='xz')
    donations_committees_concatenated.to_csv(os.path.join(DATA_PATH,
                                             time.strftime("%Y-%m-%d") +
                                             '-donations_committees.xz'),
                                             compression='xz')
