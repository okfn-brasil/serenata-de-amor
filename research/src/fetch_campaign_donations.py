import os
import shutil
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')
YEARS = range(2010, 2017, 2)


class Donation:
    """Context manager to download  a zip, read data them and cleanup"""

    URL = 'http://agencia.tse.jus.br/estatistica/sead/odsele/prestacao_contas'

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

    def __init__(self, year):
        self.year = year
        self.zip_file = self.ZIPNAMES.get(year)
        self.url = '{}/{}'.format(self.URL, self.zip_file)
        self.directory = self.DIRNAMES.get(year)
        self.path = Path(self.directory)

    def _download(self):
        """Saves file from `url` into local `path` showing a progress bar"""
        print('Downloading {}…'.format(self.url))
        request = requests.get(self.url, stream=True)
        total = int(request.headers.get('content-length', 0))
        with open(self.zip_file, 'wb') as file_handler:
            kwargs = dict(total=total, unit='B', unit_scale=True)
            bock_size = 2 ** 19  # ~ 500kB
            for data in tqdm(request.iter_content(bock_size), **kwargs):
                file_handler.write(data)

    def _unzip(self):
        print('Uncompressing {}…'.format(self.zip_file))
        with zipfile.ZipFile(self.zip_file, 'r') as zip_handler:
            zip_handler.extractall(self.directory)

    def _read_csv(self, path, chunksize=None):
        """Wrapper to read CSV with default args and an optional `chunksize`"""
        kwargs = dict(low_memory=False, encoding="ISO-8859-1", sep=';')
        if chunksize:
            kwargs['chunksize'] = 10000

        data = pd.read_csv(path, **kwargs)
        return pd.concat([chunk for chunk in data]) if chunksize else data

    def _data_by_pattern(self, *patterns):
        """
        Given a list of words, loads all files matching these words, and then
        concats them all in a single data frame
        """
        pattern = '*{}*'.format('*'.join(patterns))
        data = [self._read_csv(name) for name in self.path.glob(pattern)]
        return pd.concat(data)

    def data(self):
        """
        Returns a dictionary with data frames for candidates, parties and
        committees
        """
        files = self.FILENAMES.get(year)
        if not files:  # it's 2010, a different file architecture
            return {
                'candidates': self._data_by_pattern('Receitas', 'candidato'),
                'parties': self._data_by_pattern('Receitas', 'partido'),
                'committees': self._data_by_pattern('Receitas', 'comite')
            }

        paths = (os.path.join(self.directory, filename) for filename in files)
        keys = ('candidates', 'parties', 'committees')
        return {
            key: self._read_csv(path, chunksize=10000)
            for path, key in zip(keys, paths)
        }

    def __enter__(self):
        self._download()
        self._extract()
        return self

    def __exit__(self):
        os.remove(self.zip_file)
        shutil.rmtree(self.directory)


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


def data_by_year(year):
    with Donation(year) as donation:
        data = donation.data()
        for key in ('candidates', 'parties', 'committees'):
            strip_columns_names(data, key)
        return data


if __name__ == '__main__':
    donations_data = [data_by_year(year) for year in YEARS]

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
