import os
import sys
import time
import shutil
import zipfile
import urllib.request

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')


def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize:
            sys.stderr.write("\n")
    else:
        sys.stderr.write("read %d\n" % (readsofar,))


def folder_walk_2010():
    donations_data_candidates_2010 = []
    donations_data_parties_2010 = []
    donations_data_committees_2010 = []
    for root, dirs, files in os.walk("prestacao_contas_2010", topdown=False):
        for name in files:
            if 'Receitas' in name:
                data = pd.read_csv(os.path.join(root, name), low_memory=False,
                                   encoding="ISO-8859-1", sep=';')
                if 'candidato' in os.path.join(root, name):
                    donations_data_candidates_2010.append(data)
                elif 'comite' in os.path.join(root, name):
                    donations_data_committees_2010.append(data)
                elif 'partido' in os.path.join(root, name):
                    donations_data_parties_2010.append(data)

    donations_data_candidates_2010 = pd.concat(donations_data_candidates_2010)
    donations_data_parties_2010 = pd.concat(donations_data_parties_2010)
    donations_data_committees_2010 = pd.concat(donations_data_committees_2010)
    shutil.rmtree('prestacao_contas_2010')
    return {'candidates': donations_data_candidates_2010,
            'parties': donations_data_parties_2010,
            'committees': donations_data_committees_2010}


def folder_walk_2012():
    path_candid = os.path.join('prestacao_final_2012',
                               'receitas_candidatos_2012_brasil.txt')
    path_parties = os.path.join('prestacao_final_2012',
                                'receitas_partidos_2012_brasil.txt')
    path_committ = os.path.join('prestacao_final_2012',
                                'receitas_comites_2012_brasil.txt')
    donations_data_candidates_2012_chunks = pd.read_csv(path_candid,
                                                        low_memory=True,
                                                        encoding="ISO-8859-1",
                                                        sep=';',
                                                        chunksize=10000)
    donations_data_candidates_2012 = []
    for chunk in donations_data_candidates_2012_chunks:
        donations_data_candidates_2012.append(chunk)

    donations_data_candidates_2012 = pd.concat(donations_data_candidates_2012)

    donations_data_parties_2012 = pd.read_csv(path_parties, low_memory=False,
                                              encoding="ISO-8859-1", sep=';')
    donations_data_committees_2012 = pd.read_csv(path_committ,
                                                 low_memory=False,
                                                 encoding="ISO-8859-1",
                                                 sep=';')
    shutil.rmtree('prestacao_final_2012')
    return {'candidates': donations_data_candidates_2012,
            'parties': donations_data_parties_2012,
            'committees': donations_data_committees_2012}


def folder_walk_2014():
    path_candid = os.path.join('prestacao_final_2014',
                               'receitas_candidatos_2014_brasil.txt')
    path_parties = os.path.join('prestacao_final_2014',
                                'receitas_partidos_2014_brasil.txt')
    path_committ = os.path.join('prestacao_final_2014',
                                'receitas_comites_2014_brasil.txt')
    donations_data_candidates_2014 = pd.read_csv(path_candid, low_memory=False,
                                                 encoding="ISO-8859-1",
                                                 sep=';')
    donations_data_parties_2014 = pd.read_csv(path_parties, low_memory=False,
                                              encoding="ISO-8859-1", sep=';')
    donations_data_committees_2014 = pd.read_csv(path_committ,
                                                 low_memory=False,
                                                 encoding="ISO-8859-1",
                                                 sep=';')
    shutil.rmtree('prestacao_final_2014')
    return {'candidates': donations_data_candidates_2014,
            'parties': donations_data_parties_2014,
            'committees': donations_data_committees_2014}


def folder_walk_2016():
    path_candid = os.path.join('prestacao_contas_final_2016',
                               ('receitas_candidatos_prestacao_contas_final_2016_brasil'  # noqa
                                '.txt'))
    path_parties = os.path.join('prestacao_contas_final_2016',
                                ('receitas_partidos_prestacao_contas_final_2016_brasil'  # noqa
                                 '.txt'))
    donations_data_candidates_2016_chunks = pd.read_csv(path_candid,
                                                        encoding="ISO-8859-1",
                                                        sep=';',
                                                        low_memory=True,
                                                        chunksize=10000)
    donations_data_candidates_2016 = []
    for chunk in donations_data_candidates_2016_chunks:
        donations_data_candidates_2016.append(chunk)
    donations_data_candidates_2016 = pd.concat(donations_data_candidates_2016)
    donations_data_parties_2016 = pd.read_csv(path_parties, low_memory=False,
                                              encoding="ISO-8859-1", sep=';')
    shutil.rmtree('prestacao_contas_final_2016')
    return {'candidates': donations_data_candidates_2016,
            'parties': donations_data_parties_2016}


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
                    'Setor econômico do doador': 'donor_economic_sector',
                    'Setor econômico do doador originário':
                    'original_donor_economic_sector',
                    'Sigla da UE': 'electoral_unit_abbreviation',
                    'Sigla Partido': 'party_acronym',
                    'Sigla UE doador': 'donor_electoral_unit_abbreviation',
                    'Tipo de documento': 'document_type',
                    'Tipo doador originário': 'original_donor_type',
                    'Tipo partido': 'party_type',
                    'Tipo receita': 'revenue_type',
                    'Tipo comite': 'committee_type',
                    'UF': 'state',
                    'Valor receita': 'revenue_value'}
    if 'candidates' in donations_data.keys():
        donations_data['candidates'].rename(columns={translations},
                                            inplace=True)
    if 'parties' in donations_data.keys():
        donations_data['parties'].rename(columns={translations},
                                         inplace=True)
    if 'committees' in donations_data.keys():
        donations_data['committees'].rename(columns={translations},
                                            inplace=True)


def download_base(url, folder_walk_function):
    file_name = url.split('/')[-1]
    print("Downloading " + file_name)
    urllib.request.urlretrieve(url, file_name, reporthook)
    print("Uncompressing downloaded data.")
    with zipfile.ZipFile(file_name, "r") as zip_ref:
        zip_ref.extractall(file_name.split('.')[0])
    os.remove(file_name)

    print("Reading all the data and creating the dataframes...")

    donations_data = folder_walk_function()

    if 'candidates' in donations_data.keys():
        columns_candidates = donations_data['candidates'].columns.values
        columns_mod_candidates = {}
        for name in columns_candidates:
            columns_mod_candidates[name] = name.strip()
        donations_data['candidates'].rename(columns=columns_mod_candidates,
                                            inplace=True)

    if 'parties' in donations_data.keys():
        columns_parties = donations_data['parties'].columns.values
        columns_mod_parties = {}
        for name in columns_parties:
            columns_mod_parties[name] = name.strip()
        donations_data['parties'].rename(columns=columns_mod_parties,
                                         inplace=True)

    if 'committees' in donations_data.keys():
        columns_committees = donations_data['committees'].columns.values
        columns_mod_committees = {}
        for name in columns_committees:
            columns_mod_committees[name] = name.strip()
        donations_data['committees'].rename(columns=columns_mod_committees,
                                            inplace=True)

    return donations_data

if __name__ == "__main__":
    base_url = ('http://agencia.tse.jus.br/estatistica/sead/odsele/'
                'prestacao_contas/')
    url = base_url + 'prestacao_contas_2010.zip'
    donations_data_2010 = download_base(url, folder_walk_2010)
    url = base_url + 'prestacao_final_2012.zip'
    donations_data_2012 = download_base(url, folder_walk_2012)
    url = base_url + 'prestacao_final_2014.zip'
    donations_data_2014 = download_base(url, folder_walk_2014)
    url = base_url + 'prestacao_contas_final_2016.zip'
    donations_data_2016 = download_base(url, folder_walk_2016)

    correct_columns(donations_data_2010)
    correct_columns(donations_data_2012)
    correct_columns(donations_data_2014)
    correct_columns(donations_data_2016)

    translate_columns(donations_data_2010)
    translate_columns(donations_data_2012)
    translate_columns(donations_data_2014)
    translate_columns(donations_data_2016)

    donations_candidates_concatenated = pd.concat([donations_data_2010['candidates'],  # noqa
                                                   donations_data_2012['candidates'],  # noqa
                                                   donations_data_2014['candidates'],  # noqa
                                                   donations_data_2016['candidates']])  # noqa
    donations_parties_concatenated = pd.concat([donations_data_2010['parties'],
                                                donations_data_2012['parties'],
                                                donations_data_2014['parties'],
                                                donations_data_2016['parties']])  # noqa
    donations_committees_concatenated = pd.concat([donations_data_2010['committees'],  # noqa
                                                   donations_data_2012['committees'],  # noqa
                                                   donations_data_2014['committees']])  # noqa

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
