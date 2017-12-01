import os
import shutil
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests
from tqdm import tqdm


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')
KEYS = ('candidates', 'parties', 'committees')
YEARS = range(2010, 2017, 2)


class Donation:
    """Context manager to download, read data from a given year and cleanup"""

    URL = 'http://agencia.tse.jus.br/estatistica/sead/odsele/prestacao_contas'

    ZIPNAMES = {
        2010: 'prestacao_contas_2010.zip',
        2012: 'prestacao_final_2012.zip',
        2014: 'prestacao_final_2014.zip',
        2016: 'prestacao_contas_final_2016.zip',
    }

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

    NORMALIZE_COLUMNS = {
        'candidates': {
            'Descricao da receita': 'Descrição da receita',
            'Especie recurso': 'Espécie recurso',
            'Numero candidato': 'Número candidato',
            'Numero do documento': 'Número do documento',
            'Numero Recibo Eleitoral': 'Número Recibo Eleitoral',
            'Sigla  Partido': 'Sigla Partido'
        },
        'parties': {
            'Sigla  Partido': 'Sigla Partido',
            'Número recibo eleitoral': 'Número Recibo Eleitoral'
        },
        'committees': {
            'Sigla  Partido': 'Sigla Partido',
            'Tipo comite': 'Tipo Comite',
            'Número recibo eleitoral': 'Número Recibo Eleitoral'
        }
    }

    TRANSLATIONS = {
        'Cargo': 'post',
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
        'Valor receita': 'revenue_value'
    }

    def __init__(self, year):
        self.year = year
        self.zip_file = self.ZIPNAMES.get(year)
        self.url = '{}/{}'.format(self.URL, self.zip_file)
        self.directory, _ = os.path.splitext(self.zip_file)
        self.path = Path(self.directory)

    def _download(self):
        """Saves file from `url` into local `path` showing a progress bar"""
        print('Downloading {}…'.format(self.url))
        request = requests.get(self.url, stream=True)
        total = int(request.headers.get('content-length', 0))
        with open(self.zip_file, 'wb') as file_handler:
            block_size = 2 ** 15  # ~ 32kB
            kwargs = dict(total=total, unit='B', unit_scale=True)
            with tqdm(**kwargs) as progress_bar:
                for data in request.iter_content(block_size):
                    file_handler.write(data)
                    progress_bar.update(block_size)

    def _unzip(self):
        print('Uncompressing {}…'.format(self.zip_file))
        with ZipFile(self.zip_file, 'r') as zip_handler:
            zip_handler.extractall(self.directory)

    def _read_csv(self, path, chunksize=None):
        """Wrapper to read CSV with default args and an optional `chunksize`"""
        kwargs = dict(low_memory=False, encoding="ISO-8859-1", sep=';')
        if chunksize:
            kwargs['chunksize'] = 10000

        data = pd.read_csv(path, **kwargs)
        return pd.concat([chunk for chunk in data]) if chunksize else data

    def _data_by_pattern(self, pattern):
        """
        Given a glob pattern, loads all files matching this pattern, and then
        concats them all in a single data frame
        """
        data = [self._read_csv(name) for name in self.path.glob(pattern)]
        return pd.concat(data)

    def _data(self):
        """
        Returns a dictionary with data frames for candidates, parties and
        committees
        """
        files = self.FILENAMES.get(self.year)
        if not files:  # it's 2010, a different file architecture
            return {
                'candidates': self._data_by_pattern('**/ReceitasCandidatos*'),
                'parties': self._data_by_pattern('**/ReceitasPartidos*'),
                'committees': self._data_by_pattern('**/ReceitasComites*')
            }

        paths = (
            os.path.join(self.directory, filename)
            for filename in files
            if filename
        )
        return {
            key: self._read_csv(path, chunksize=10000)
            for key, path in zip(KEYS, paths)
            if os.path.exists(path)
        }

    @property
    def data(self):
        """Takes self._data, clean, normalizes and translate it"""
        data = self._data()
        for key in KEYS:
            normalize_columns = self.NORMALIZE_COLUMNS.get(key)
            if key in data:
                # strip columns names ('foobar ' -> 'foobar')
                names = data[key].columns.values
                cleaned_columns = {name: name.strip() for name in names}
                data[key].rename(columns=cleaned_columns, inplace=True)
                # normalize & translate
                data[key].rename(columns=normalize_columns, inplace=True)
                data[key].rename(columns=self.TRANSLATIONS, inplace=True)
        return data

    def __enter__(self):
        self._download()
        self._unzip()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print('Cleaning up source files from {}…'.format(self.year))
        os.remove(self.zip_file)
        shutil.rmtree(self.directory)


def save(key, data):
    """Given a key and a data frame, saves it compressed in LZMA"""
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    prefix = date.today().strftime('%Y-%m-%d')
    filename = '{}-donations-{}.xz'.format(prefix, key)
    print('Saving {}…'.format(filename))
    data.to_csv(os.path.join(DATA_PATH, filename), compression='xz')


def fetch_data_from(year):
    with Donation(year) as donation:
        return donation.data


if __name__ == '__main__':
    by_year = tuple(fetch_data_from(year) for year in YEARS)
    for key in KEYS:
        data = pd.concat([
            dataframes.get(key) for dataframes in by_year
            if isinstance(dataframes.get(key), pd.DataFrame)
        ])
        save(key, data)
