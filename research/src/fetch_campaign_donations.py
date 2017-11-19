import os
import shutil
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')

BASE_URL = 'http://agencia.tse.jus.br/estatistica/sead/odsele/prestacao_contas'
YEARS = range(2010, 2017, 2)

DIRNAMES = {
    2010: 'prestacao_contas_2010',
    2012: 'prestacao_final_2010',
    2014: 'prestacao_final_2014',
    2016: 'prestacao_contas_final_2016',
}

ZIPNAMES = {key: '{}.zip'.format(value) for key, value in DIRNAMES.items()}

FILENAMES = {
    2012: (
        'receitas_candidatos_2012_brasil.txt',
        'receitas_partidos_2012_brasil.txt',
        'receitas_comites_2012_brasil.txt'
    ),
    2014: (
        'receitas_candidatos_2014_brasil.txt',
        'receitas_partidos_2014_brasil.txt',
        'receitas_comites_2014_brasil.txt'
    ),
    2016: (
        'receitas_candidatos_prestacao_contas_final_2016_brasil.txt',
        'receitas_partidos_prestacao_contas_final_2016_brasil.txt',
        None
    )
}

READ_KWARGS = dict(
    low_memory=False,
    encoding="ISO-8859-1",
    sep=';'
)
DOWNLOAD_BOCK_SIZE = 2 ** 19  # ~ 500kB


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
    return pd.concat([chunk for chunk in data]) if chunksize else data


class ReadAndRemove:
    """Context manager to read a directory and then delete it"""

    def __init__(self, directory):
        self.directory = directory
        self.path = Path(directory)

    def data_for(self, *patterns):
        """
        Given a list of words, loads all files matching these words, and then
        concats them all in a single data frame
        """
        pattern = '*{}*'.format('*'.join(patterns))
        data = [read_csv(filename) for filename in self.path.glob(pattern)]
        return pd.concat(data)

    def __enter__(self):
        return self

    def __exit__(self):
        shutil.rmtree(self.directory)


@contextmanager
def paths_by_year(year):
    """For 2012-2016 return the paths of the relevant files"""
    directory = DIRNAMES.get(year)
    yield (os.path.join(directory, f) for f in FILENAMES.get(year))
    shutil.rmtree(directory)


def folder_walk(year):
    if year == 2010:
        with ReadAndRemove(DIRNAMES.get(year)) as dir:
            return {
                'candidates': dir.data_for('Receitas', 'candidato'),
                'parties': dir.data_for('Receitas', 'comite'),
                'committees': dir.data_for('Receitas', 'partido')
            }

    with paths_by_year(year) as paths:
        candidates, parties, committees = paths
        return {
            'candidates': read_csv(candidates, 10000),
            'parties': read_csv(parties, 10000),
            'committees': read_csv(committees, 10000) if committees else None
        }


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


def download_year(year):
    file_name = ZIPNAMES.get(year)
    url = '{}/{}'.format(BASE_URL, file_name)
    print('Downloading {}…'.format(file_name))
    download(url, file_name)

    print("Uncompressing downloaded data…")
    with zipfile.ZipFile(file_name, "r") as zip_ref:
        zip_ref.extractall(DIRNAMES.get(year))
    os.remove(file_name)

    print("Reading all the data and creating the dataframes…")

    donations_data = folder_walk(year)

    strip_columns_names(donations_data, 'candidates')
    strip_columns_names(donations_data, 'parties')
    strip_columns_names(donations_data, 'committees')

    return donations_data


if __name__ == "__main__":
    donations_data = [download_year(year) for year in YEARS]

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
