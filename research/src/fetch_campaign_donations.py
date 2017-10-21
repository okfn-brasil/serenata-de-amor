import pandas as pd
import urllib.request
import os        
import sys
import zipfile
import time

def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else: # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))
        
url = 'http://agencia.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_contas_2010.zip'
file_name = 'prestacao_contas_2010.zip'
print("Downloading 2010 donation data...")
urllib.request.urlretrieve(url, file_name, reporthook)

print("Uncompressing downloaded data.")
with zipfile.ZipFile('prestacao_contas_2010.zip',"r") as zip_ref:
    zip_ref.extractall("prestacao_contas_2010")
os.remove("prestacao_contas_2010.zip")

url = 'http://agencia.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_final_2012.zip'
file_name = 'prestacao_final_2012.zip'
print("Downloading 2012 donation data...")
urllib.request.urlretrieve(url, file_name, reporthook)

print("Uncompressing downloaded data.")
with zipfile.ZipFile('prestacao_final_2012.zip',"r") as zip_ref:
    zip_ref.extractall("prestacao_final_2012")
os.remove("prestacao_final_2012.zip")

url = 'http://agencia.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_final_2014.zip'
file_name = 'prestacao_final_2014.zip'
print("Downloading 2014 donation data...")
urllib.request.urlretrieve(url, file_name, reporthook)

print("Uncompressing downloaded data.")
with zipfile.ZipFile('prestacao_final_2014.zip',"r") as zip_ref:
    zip_ref.extractall("prestacao_final_2014")
os.remove("prestacao_final_2014.zip")

url = 'http://agencia.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_contas_final_2016.zip'
file_name = 'prestacao_contas_final_2016.zip'
print("Downloading 2016 donation data...")
urllib.request.urlretrieve(url, file_name, reporthook)

print("Uncompressing downloaded data.")
with zipfile.ZipFile('prestacao_contas_final_2016.zip',"r") as zip_ref:
    zip_ref.extractall("prestacao_contas_final_2016")
os.remove("prestacao_contas_final_2016.zip")

print("Reading all the data and creating the dataframes...")

donations_data_candidates_2010 = []
donations_data_parties_2010 = []
donations_data_committees_2010 = []
for root, dirs, files in os.walk("prestacao_contas_2010/", topdown=False):
    for name in files:
        if 'Receitas' in name:
            data = pd.read_csv(os.path.join(root, name), low_memory=False, encoding = "ISO-8859-1", sep = ';')
            if '/candidato/' in os.path.join(root, name):
                donations_data_candidates_2010.append(data)
            elif '/comite/' in os.path.join(root, name):
                donations_data_committees_2010.append(data)
            elif '/partido/' in os.path.join(root, name):
                donations_data_parties_2010.append(data)
                
donations_data_candidates_2010 = pd.concat(donations_data_candidates_2010)
donations_data_parties_2010 = pd.concat(donations_data_parties_2010)
donations_data_committees_2010 = pd.concat(donations_data_committees_2010)

donations_data_candidates_2012_chunks = pd.read_csv('prestacao_final_2012/receitas_candidatos_2012_brasil.txt',
                                                    low_memory=True, encoding = "ISO-8859-1", sep = ';',
                                                    chunksize = 10000)
donations_data_candidates_2012 = []
for chunk in donations_data_candidates_2012_chunks:
    donations_data_candidates_2012.append(chunk)
    
donations_data_candidates_2012 = pd.concat(donations_data_candidates_2012)

donations_data_parties_2012 = pd.read_csv('prestacao_final_2012/receitas_partidos_2012_brasil.txt', low_memory=False,
                                          encoding = "ISO-8859-1", sep = ';')
donations_data_committees_2012 = pd.read_csv('prestacao_final_2012/receitas_comites_2012_brasil.txt', low_memory=False,
                                             encoding = "ISO-8859-1", sep = ';')
                                             
                                             donations_data_candidates_2014 = pd.read_csv('prestacao_final_2014/receitas_candidatos_2014_brasil.txt', low_memory=False,
                                             encoding = "ISO-8859-1", sep = ';')
donations_data_parties_2014 = pd.read_csv('prestacao_final_2014/receitas_partidos_2014_brasil.txt', low_memory=False,
                                           encoding = "ISO-8859-1", sep = ';')
donations_data_committees_2014 = pd.read_csv('prestacao_final_2014/receitas_comites_2014_brasil.txt', low_memory=False,
                                          encoding = "ISO-8859-1", sep = ';')
                                          
                                          donations_data_candidates_2016_chunks = pd.read_csv('prestacao_contas_final_2016/receitas_candidatos_prestacao_contas_final_2016_brasil.txt',
                                             encoding = "ISO-8859-1", sep = ';', low_memory=True, chunksize=10000)

donations_data_candidates_2016 = []
for chunk in donations_data_candidates_2016_chunks:
    donations_data_candidates_2016.append(chunk)
    
donations_data_candidates_2016 = pd.concat(donations_data_candidates_2016)

donations_data_parties_2016 = pd.read_csv('prestacao_contas_final_2016/receitas_partidos_prestacao_contas_final_2016_brasil.txt',
                                          low_memory=False, encoding = "ISO-8859-1", sep = ';')
                                          
 columns_candidates_2010 = donations_data_candidates_2010.columns.values
columns_candidates_2012 = donations_data_candidates_2012.columns.values
columns_candidates_2014 = donations_data_candidates_2014.columns.values
columns_candidates_2016 = donations_data_candidates_2016.columns.values
columns_parties_2010 = donations_data_parties_2010.columns.values
columns_parties_2012 = donations_data_parties_2012.columns.values
columns_parties_2014 = donations_data_parties_2014.columns.values
columns_parties_2016 = donations_data_parties_2016.columns.values
columns_committees_2010 = donations_data_committees_2010.columns.values
columns_committees_2012 = donations_data_committees_2012.columns.values
columns_committees_2014 = donations_data_committees_2014.columns.values

columns_mod_candidates_2010 = {}
columns_mod_candidates_2012 = {}
columns_mod_candidates_2014 = {}
columns_mod_candidates_2016 = {}
columns_mod_parties_2010 = {}
columns_mod_parties_2012 = {}
columns_mod_parties_2014 = {}
columns_mod_parties_2016 = {}
columns_mod_committees_2010 = {}
columns_mod_committees_2012 = {}
columns_mod_committees_2014 = {}

for name in columns_candidates_2010:
    columns_mod_candidates_2010[name] = name.strip()
for name in columns_candidates_2012:
    columns_mod_candidates_2012[name] = name.strip()
for name in columns_candidates_2014:
    columns_mod_candidates_2014[name] = name.strip()
for name in columns_candidates_2016:
    columns_mod_candidates_2016[name] = name.strip()
for name in columns_parties_2010:
    columns_mod_parties_2010[name] = name.strip()
for name in columns_parties_2012:
    columns_mod_parties_2012[name] = name.strip()
for name in columns_parties_2014:
    columns_mod_parties_2014[name] = name.strip()
for name in columns_parties_2016:
    columns_mod_parties_2016[name] = name.strip()
for name in columns_committees_2010:
    columns_mod_committees_2010[name] = name.strip()
for name in columns_committees_2012:
    columns_mod_committees_2012[name] = name.strip()
for name in columns_committees_2014:
    columns_mod_committees_2014[name] = name.strip()

# General strips
donations_data_candidates_2010.rename(columns=columns_mod_candidates_2010, inplace=True)
donations_data_parties_2010.rename(columns=columns_mod_parties_2010, inplace=True)
donations_data_committees_2010.rename(columns=columns_mod_committees_2010, inplace=True)
donations_data_candidates_2012.rename(columns=columns_mod_candidates_2012, inplace=True)
donations_data_parties_2012.rename(columns=columns_mod_parties_2012, inplace=True)
donations_data_committees_2012.rename(columns=columns_mod_committees_2012, inplace=True)
donations_data_candidates_2014.rename(columns=columns_mod_candidates_2014, inplace=True)
donations_data_parties_2014.rename(columns=columns_mod_parties_2014, inplace=True)
donations_data_committees_2014.rename(columns=columns_mod_committees_2014, inplace=True)
donations_data_candidates_2016.rename(columns=columns_mod_candidates_2016, inplace=True)
donations_data_parties_2016.rename(columns=columns_mod_parties_2016, inplace=True)

# Specific renaming cases
donations_data_candidates_2010.rename(columns={'Descricao da receita': 'Descrição da receita'}, inplace=True)
donations_data_candidates_2012.rename(columns={'Descricao da receita': 'Descrição da receita'}, inplace=True)
donations_data_candidates_2014.rename(columns={'Descricao da receita': 'Descrição da receita'}, inplace=True)
donations_data_candidates_2016.rename(columns={'Descricao da receita': 'Descrição da receita'}, inplace=True)

donations_data_candidates_2010.rename(columns={'Especie recurso': 'Espécie recurso'}, inplace=True)
donations_data_candidates_2012.rename(columns={'Especie recurso': 'Espécie recurso'}, inplace=True)
donations_data_candidates_2014.rename(columns={'Especie recurso': 'Espécie recurso'}, inplace=True)
donations_data_candidates_2016.rename(columns={'Especie recurso': 'Espécie recurso'}, inplace=True)

donations_data_candidates_2010.rename(columns={'Numero candidato': 'Número candidato'}, inplace=True)
donations_data_candidates_2012.rename(columns={'Numero candidato': 'Número candidato'}, inplace=True)
donations_data_candidates_2014.rename(columns={'Numero candidato': 'Número candidato'}, inplace=True)
donations_data_candidates_2016.rename(columns={'Numero candidato': 'Número candidato'}, inplace=True)

donations_data_candidates_2010.rename(columns={'Numero do documento': 'Número do documento'}, inplace=True)
donations_data_candidates_2012.rename(columns={'Numero do documento': 'Número do documento'}, inplace=True)
donations_data_candidates_2014.rename(columns={'Numero do documento': 'Número do documento'}, inplace=True)
donations_data_candidates_2016.rename(columns={'Numero do documento': 'Número do documento'}, inplace=True)

donations_data_candidates_2010.rename(columns={'Numero Recibo Eleitoral': 'Número Recibo Eleitoral'}, inplace=True)
donations_data_candidates_2012.rename(columns={'Numero Recibo Eleitoral': 'Número Recibo Eleitoral'}, inplace=True)
donations_data_candidates_2014.rename(columns={'Numero Recibo Eleitoral': 'Número Recibo Eleitoral'}, inplace=True)
donations_data_candidates_2016.rename(columns={'Numero Recibo Eleitoral': 'Número Recibo Eleitoral'}, inplace=True)

donations_data_candidates_2010.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_candidates_2012.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_candidates_2014.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_candidates_2016.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)

donations_data_parties_2010.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_parties_2012.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_parties_2014.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_parties_2016.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)

donations_data_committees_2010.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_committees_2012.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)
donations_data_committees_2014.rename(columns={'Sigla  Partido': 'Sigla Partido'}, inplace=True)

donations_data_committees_2010.rename(columns={'Tipo comite': 'Tipo Comite'}, inplace=True)
donations_data_committees_2012.rename(columns={'Tipo comite': 'Tipo Comite'}, inplace=True)
donations_data_committees_2014.rename(columns={'Tipo comite': 'Tipo Comite'}, inplace=True)

donations_data_committees_2010.rename(columns={'Número recibo eleitoral': 'Número Recibo Eleitoral'}, inplace=True)
donations_data_committees_2012.rename(columns={'Número recibo eleitoral': 'Número Recibo Eleitoral'}, inplace=True)
donations_data_committees_2014.rename(columns={'Número recibo eleitoral': 'Número Recibo Eleitoral'}, inplace=True)

donations_candidates_concatenated = pd.concat([donations_data_candidates_2010, donations_data_candidates_2012,
                                               donations_data_candidates_2014, donations_data_candidates_2016])
donations_parties_concatenated = pd.concat([donations_data_parties_2010, donations_data_parties_2012,
                                            donations_data_parties_2014, donations_data_parties_2016])
donations_committees_concatenated = pd.concat([donations_data_committees_2010, donations_data_committees_2012,
                                               donations_data_committees_2014])
                                               
donations_candidates_concatenated.rename(columns={'Cargo': 'post'}, inplace=True)
donations_candidates_concatenated.rename(columns={'CNPJ Prestador Conta': 'accountable_company_id'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Cod setor econômico do doador': 'donor_economic_setor_id'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Cód. Eleição': 'election_id'}, inplace=True)
donations_candidates_concatenated.rename(columns={'CPF do candidato': 'candidate_cpf'}, inplace=True)
donations_candidates_concatenated.rename(columns={'CPF do vice/suplente': 'substitute_cpf'}, inplace=True)
donations_candidates_concatenated.rename(columns={'CPF/CNPJ do doador': 'donor_cnpj_or_cpf'}, inplace=True)
donations_candidates_concatenated.rename(columns={'CPF/CNPJ do doador originário': 'original_donor_cnpj_or_cpf'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Data da receita': 'revenue_date'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Data e hora': 'date_and_time'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Desc. Eleição': 'election_description'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Descrição da receita': 'revenue_description'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Entrega em conjunto?': 'batch'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Especie recurso': 'type_of_revenue'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Fonte recurso': 'source_of_revenue'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Municipio': 'city'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Nome candidato': 'candidate_name'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Nome da UE': 'electoral_unit_name'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Nome do doador': 'donor_name'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Nome do doador (Receita Federal)': 'donor_name_for_federal_revenue'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Nome do doador originário': 'original_donor_name'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Nome do doador originário (Receita Federal)': 'original_donor_name_for_federal_revenue'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Numero candidato': 'candidate_number'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Número candidato doador': 'donor_candidate_number'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Numero do documento': 'document_number'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Número partido doador': 'donor_party_number'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Numero Recibo Eleitoral': 'electoral_receipt_number'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Numero UE': 'electoral_unit_number'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Sequencial Candidato': 'candidate_sequence'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Setor econômico do doador': 'donor_economic_sector'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Setor econômico do doador originário': 'original_donor_economic_sector'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Sigla da UE': 'electoral_unit_abbreviation'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Sigla Partido': 'party_acronym'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Sigla UE doador': 'donor_electoral_unit_abbreviation'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Tipo doador originário': 'original_donor_type'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Tipo receita': 'revenue_type'}, inplace=True)
donations_candidates_concatenated.rename(columns={'UF': 'state'}, inplace=True)
donations_candidates_concatenated.rename(columns={'Valor receita': 'revenue_value'}, inplace=True)
donations_parties_concatenated.rename(columns={'Cargo': 'post'}, inplace=True)
donations_parties_concatenated.rename(columns={'CNPJ Prestador Conta': 'accountable_company_id'}, inplace=True)
donations_parties_concatenated.rename(columns={'Cod setor econômico do doador': 'donor_economic_setor_id'}, inplace=True)
donations_parties_concatenated.rename(columns={'Cód. Eleição': 'election_id'}, inplace=True)
donations_parties_concatenated.rename(columns={'CPF do candidato': 'candidate_cpf'}, inplace=True)
donations_parties_concatenated.rename(columns={'CPF do vice/suplente': 'substitute_cpf'}, inplace=True)
donations_parties_concatenated.rename(columns={'CPF/CNPJ do doador': 'donor_cnpj_or_cpf'}, inplace=True)
donations_parties_concatenated.rename(columns={'CPF/CNPJ do doador originário': 'original_donor_cnpj_or_cpf'}, inplace=True)
donations_parties_concatenated.rename(columns={'Data da receita': 'revenue_date'}, inplace=True)
donations_parties_concatenated.rename(columns={'Data e hora': 'date_and_time'}, inplace=True)
donations_parties_concatenated.rename(columns={'Desc. Eleição': 'election_description'}, inplace=True)
donations_parties_concatenated.rename(columns={'Descrição da receita': 'revenue_description'}, inplace=True)
donations_parties_concatenated.rename(columns={'Entrega em conjunto?': 'batch'}, inplace=True)
donations_parties_concatenated.rename(columns={'Especie recurso': 'type_of_revenue'}, inplace=True)
donations_parties_concatenated.rename(columns={'Fonte recurso': 'source_of_revenue'}, inplace=True)
donations_parties_concatenated.rename(columns={'Municipio': 'city'}, inplace=True)
donations_parties_concatenated.rename(columns={'Nome candidato': 'candidate_name'}, inplace=True)
donations_parties_concatenated.rename(columns={'Nome da UE': 'electoral_unit_name'}, inplace=True)
donations_parties_concatenated.rename(columns={'Nome do doador': 'donor_name'}, inplace=True)
donations_parties_concatenated.rename(columns={'Nome do doador (Receita Federal)': 'donor_name_for_federal_revenue'}, inplace=True)
donations_parties_concatenated.rename(columns={'Nome do doador originário': 'original_donor_name'}, inplace=True)
donations_parties_concatenated.rename(columns={'Nome do doador originário (Receita Federal)': 'original_donor_name_for_federal_revenue'}, inplace=True)
donations_parties_concatenated.rename(columns={'Numero candidato': 'candidate_number'}, inplace=True)
donations_parties_concatenated.rename(columns={'Número candidato doador': 'donor_candidate_number'}, inplace=True)
donations_parties_concatenated.rename(columns={'Numero do documento': 'document_number'}, inplace=True)
donations_parties_concatenated.rename(columns={'Número partido doador': 'donor_party_number'}, inplace=True)
donations_parties_concatenated.rename(columns={'Numero Recibo Eleitoral': 'electoral_receipt_number'}, inplace=True)
donations_parties_concatenated.rename(columns={'Numero UE': 'electoral_unit_number'}, inplace=True)
donations_parties_concatenated.rename(columns={'Sequencial Candidato': 'candidate_sequence'}, inplace=True)
donations_parties_concatenated.rename(columns={'Setor econômico do doador': 'donor_economic_sector'}, inplace=True)
donations_parties_concatenated.rename(columns={'Setor econômico do doador originário': 'original_donor_economic_sector'}, inplace=True)
donations_parties_concatenated.rename(columns={'Sigla da UE': 'electoral_unit_abbreviation'}, inplace=True)
donations_parties_concatenated.rename(columns={'Sigla Partido': 'party_acronym'}, inplace=True)
donations_parties_concatenated.rename(columns={'Sigla UE doador': 'donor_electoral_unit_abbreviation'}, inplace=True)
donations_parties_concatenated.rename(columns={'Tipo doador originário': 'original_donor_type'}, inplace=True)
donations_parties_concatenated.rename(columns={'Tipo receita': 'revenue_type'}, inplace=True)
donations_parties_concatenated.rename(columns={'UF': 'state'}, inplace=True)
donations_parties_concatenated.rename(columns={'Valor receita': 'revenue_value'}, inplace=True)
donations_committees_concatenated.rename(columns={'Cargo': 'post'}, inplace=True)
donations_committees_concatenated.rename(columns={'CNPJ Prestador Conta': 'accountable_company_id'}, inplace=True)
donations_committees_concatenated.rename(columns={'Cod setor econômico do doador': 'donor_economic_setor_id'}, inplace=True)
donations_committees_concatenated.rename(columns={'Cód. Eleição': 'election_id'}, inplace=True)
donations_committees_concatenated.rename(columns={'CPF do candidato': 'candidate_cpf'}, inplace=True)
donations_committees_concatenated.rename(columns={'CPF do vice/suplente': 'substitute_cpf'}, inplace=True)
donations_committees_concatenated.rename(columns={'CPF/CNPJ do doador': 'donor_cnpj_or_cpf'}, inplace=True)
donations_committees_concatenated.rename(columns={'CPF/CNPJ do doador originário': 'original_donor_cnpj_or_cpf'}, inplace=True)
donations_committees_concatenated.rename(columns={'Data da receita': 'revenue_date'}, inplace=True)
donations_committees_concatenated.rename(columns={'Data e hora': 'date_and_time'}, inplace=True)
donations_committees_concatenated.rename(columns={'Desc. Eleição': 'election_description'}, inplace=True)
donations_committees_concatenated.rename(columns={'Descrição da receita': 'revenue_description'}, inplace=True)
donations_committees_concatenated.rename(columns={'Entrega em conjunto?': 'batch'}, inplace=True)
donations_committees_concatenated.rename(columns={'Espécie recurso': 'type_of_revenue'}, inplace=True)
donations_committees_concatenated.rename(columns={'Fonte recurso': 'source_of_revenue'}, inplace=True)
donations_committees_concatenated.rename(columns={'Município': 'city'}, inplace=True)
donations_committees_concatenated.rename(columns={'Nome candidato': 'candidate_name'}, inplace=True)
donations_committees_concatenated.rename(columns={'Nome da UE': 'electoral_unit_name'}, inplace=True)
donations_committees_concatenated.rename(columns={'Nome do doador': 'donor_name'}, inplace=True)
donations_committees_concatenated.rename(columns={'Nome do doador (Receita Federal)': 'donor_name_for_federal_revenue'}, inplace=True)
donations_committees_concatenated.rename(columns={'Nome do doador originário': 'original_donor_name'}, inplace=True)
donations_committees_concatenated.rename(columns={'Nome do doador originário (Receita Federal)': 'original_donor_name_for_federal_revenue'}, inplace=True)
donations_committees_concatenated.rename(columns={'Número candidato': 'candidate_number'}, inplace=True)
donations_committees_concatenated.rename(columns={'Número candidato doador': 'donor_candidate_number'}, inplace=True)
donations_committees_concatenated.rename(columns={'Número do documento': 'document_number'}, inplace=True)
donations_committees_concatenated.rename(columns={'Número partido doador': 'donor_party_number'}, inplace=True)
donations_committees_concatenated.rename(columns={'Número Recibo Eleitoral': 'electoral_receipt_number'}, inplace=True)
donations_committees_concatenated.rename(columns={'Número UE': 'electoral_unit_number'}, inplace=True)
donations_committees_concatenated.rename(columns={'Sequencial Candidato': 'candidate_sequence'}, inplace=True)
donations_committees_concatenated.rename(columns={'Setor econômico do doador': 'donor_economic_sector'}, inplace=True)
donations_committees_concatenated.rename(columns={'Setor econômico do doador originário': 'original_donor_economic_sector'}, inplace=True)
donations_committees_concatenated.rename(columns={'Sigla da UE': 'electoral_unit_abbreviation'}, inplace=True)
donations_committees_concatenated.rename(columns={'Sigla Partido': 'party_acronym'}, inplace=True)
donations_committees_concatenated.rename(columns={'Sigla UE doador': 'donor_electoral_unit_abbreviation'}, inplace=True)
donations_committees_concatenated.rename(columns={'Tipo doador originário': 'original_donor_type'}, inplace=True)
donations_committees_concatenated.rename(columns={'Tipo receita': 'revenue_type'}, inplace=True)
donations_committees_concatenated.rename(columns={'UF': 'state'}, inplace=True)
donations_committees_concatenated.rename(columns={'Valor receita': 'revenue_value'}, inplace=True)

print("Saving dataframes in csv files (.xz)...")

donations_candidates_concatenated.to_csv(time.strftime("%Y-%m-%d") + '-donations_candidates.xz', compression='xz')
donations_parties_concatenated.to_csv(time.strftime("%Y-%m-%d") + '-donations_parties.xz', compression='xz')
donations_committees_concatenated.to_csv(time.strftime("%Y-%m-%d") + '-donations_committees.xz', compression='xz')
