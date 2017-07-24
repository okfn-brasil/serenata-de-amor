""""
This script downloads and format some data from TSE website.
The first objective with this data is to obtain a list of *members of parties* in Brazil.
In *july* 2017, the data available in TSE website contained information about *membership and disfellowship in brazilian parties of each state.*
The data is available in csv format*. On TSE's website, you have to filter choosing party and state.*
The csv files from TSE contain headers.
*All the csv files present the same header, which we have translated below, so more people can access and reuse the code of Serenata Project.*
"""

import pandas as pd
import numpy as np
import os
import urllib
import zipfile
import glob

from tempfile import mkdtemp
TEMP_PATH = mkdtemp()

FILENAME_PREFIX = 'filiados_'
TSE_PARTYMEMBERS_STATE_URL = 'http://agencia.tse.jus.br/estatistica/sead/eleitorado/filiados/uf/filiados_'
TODAY = pd.datetime.today().date()
OUTPUT_FILENAME = TODAY.isoformat() + '-tse-partymembers.xz'
OUTPUT_DATASET_PATH = os.path.join(os.pardir, 'data', OUTPUT_FILENAME)
# the array with parties has considered all mentioned on TSE's website until 21/07/2017
party_list = [DEM, NOVO, PEN, PC_DO_B, PCB, PCO, PDT, PHS, PMDB, PMB, PMN, PP, PPL, PPS, PR, PRB, PROS, PRP, PRTB, PSB, PSC, PSD, PSDB, PSDC, PSL, PSOL, PSTU, PT, PT_DO_B, PTB, PTC, PTN, PV, REDE, SD]
state_list = [RS, SC, PR, RJ, SP, ES, MG, GO, DF, TO, MS, MT, AM, AC, RO, RR, PA, AP, MA, AL, PI, RN, PE, CE, SE, BA, PB]

# Download files
for party in party_list:
for state in state_list:
    filename = '{}{}.zip'.format(FILENAME_PREFIX, party, state)
    file_url = TSE_PARTYMEMBERS_STATE_URL + filename
    output_file = os.path.join(TEMP_PATH, filename)
    urllib.request.urlretrieve(file_url, output_file)

# Unzip downloaded files
for party in party_list:
for state in state_list:
    filename = FILENAME_PREFIX + party + state + '.zip'
    filepath = os.path.join(TEMP_PATH, filename)
    zip_ref = zipfile.ZipFile(filepath, 'r')
    zip_ref.extractall(TEMP_PATH)
    zip_ref.close()

# ### Adding the headers
# The following headers were extracted from LEIAME.pdf in leiame.pdf
# headers commented with (*) can be used in the future to integrate with
# other TSE datasets
header_filiados = [
    "DATA_DA_EXTRACAO"
    "HORA_DA_EXTRACAO",    
    "NUMERO_DA_INSCRICAO", #*
    "NOME_DO_FILIADO", #*
    "SIGLA_DO_PARTIDO", #*   
    "NOME_DO_PARTIDO", 
    "UF", #*
    "CODIGO_DO_MUNICIPIO", 
    "NOME_DO_MUNICIPIO",   
    "ZONA_ELEITORAL",  
    "SECAO_ELEITORAL", 
    "DATA_DA_FILIACAO",    
    "SITUACAO_DO_REGISTRO",  
    "TIPO_DO_REGISTRO",    
    "DATA_DO_PROCESSAMENTO",   
    "DATA_DA_DESFILIACAO", 
    "DATA_DO_CANCELAMENTO",    
    "DATA_DA_REGULARIZACAO",   
    "MOTIVO_DO_CANCELAMENTO",
]

# About the script below: I've no clue how I would integrate this part of consultacand together with filiados
# I don't think it applies for this scraper, because we don't have differents headers. We do need loops for parties and states though 

# Concatenate all files in one pandas dataframe
# cand_df = pd.DataFrame()
# for party in party_list:
# for state in state_list:
#     filesname = FILENAME_PREFIX + party + state + '*.txt'
#     filespath = os.path.join(TEMP_PATH, filesname)
#     files_of_the_year = sorted(glob.glob(filespath))
#     for file_i in files_of_the_year:
#         # the following cases do not take into account next elections.
#         # hopefully, TSE will add headers to the files
#         if ('2014' in file_i) or ('2016' in file_i):
#             cand_df_i = pd.read_csv(
#                 file_i,
#                 sep=';',
#                 header=None,
#                 dtype=np.str,
#                 names=header_consulta_cand_from2014,
#                 encoding='iso-8859-1')
#         elif ('2012' in file_i):
#             cand_df_i = pd.read_csv(
#                 file_i,
#                 sep=';',
#                 header=None,
#                 dtype=np.str,
#                 names=header_consulta_cand_at2012,
#                 encoding='iso-8859-1')
#         else:
#             cand_df_i = pd.read_csv(
#                 file_i,
#                 sep=';',
#                 header=None,
#                 dtype=np.str,
#                 names=header_consulta_cand_till2010,
#                 encoding='iso-8859-1')
#         cand_df = cand_df.append(cand_df_i[sel_columns])

# this index contains no useful information
# cand_df.index = cand_df.reset_index().index

# Translation
headers_translation = {
    "DATA_DA_EXTRACAO": "download date";
    "HORA_DA_EXTRACAO": "download hour",    
    "NUMERO_DA_INSCRICAO": "electoral registration number", 
    "NOME_DO_FILIADO": "party member name", 
    "SIGLA_DO_PARTIDO": "party",    
    "NOME_DO_PARTIDO": "party full name", 
    "UF": "state",  
    "CODIGO_DO_MUNICIPIO": "city code", 
    "NOME_DO_MUNICIPIO": "city",   
    "ZONA_ELEITORAL": "electoral zone",  
    "SECAO_ELEITORAL": "electoral section", 
    "DATA_DA_FILIACAO": "membership day",    
    "SITUACAO_DO_REGISTRO": "membership status",    
    "TIPO_DO_REGISTRO": "membership type",    
    "DATA_DO_PROCESSAMENTO": "processing day of membership",   
    "DATA_DA_DESFILIACAO": "disfellowship day", 
    "DATA_DO_CANCELAMENTO": "membership cancelation day",    
    "DATA_DA_REGULARIZACAO": "membership regulation day",   
    "MOTIVO_DO_CANCELAMENTO": "reason cancelation membership",
}

cand_df = cand_df.rename(columns=headers_translation)
cand_df.post = cand_df.post.map(post_translation)
cand_df.result = cand_df.result.map(result_translation)

# Exporting data
cand_df.to_csv(
    OUTPUT_DATASET_PATH,
    encoding='utf-8',
    compression='xz',
    header=True,
    index=False)
