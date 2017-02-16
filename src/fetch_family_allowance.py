import datetime
import warnings
import requests
import zipfile
from urllib.request import urlretrieve
import os
import pandas
import fileinput
from sqlalchemy import create_engine
import sys
import shutil

STARTING_YEAR = 2011

NOW = datetime.datetime.now()

SERVER = 'http://arquivos.portaldatransparencia.gov.br/'
PATH = 'downloads.asp?a={}&m={:02d}&consulta=BolsaFamiliaFolhaPagamento'

BASE_DATA_DIR = '../data/'
TEMP_DATA = "../data/temp_data/"


COLLUNM_DATA = ['UF', 'CODIGO', 'SIAFI_MUNICIPIO', 'NOME_MUNICIPIO', 'CODIGO_FUNCAO', 'CODIGO_SUBFUNCAO', 'CODIGO_PROGRAMA', 'CODIGO_ACAO',
                 'NIS_FAVORECIDO', 'NOME_FAVORECIDO', 'FONTE_FINALIDADE', 'VALOR_PARCELA', 'MES_COMPETENCIA']


def dlProgress(count, blockSize, totalSize):
  percent = int(count*blockSize*100/totalSize)
  sys.stdout.write("\r" + "progress" + "...%d%%" % percent)
  sys.stdout.flush()



def urls():
    for year in range(STARTING_YEAR, NOW.year + 1):
        for month in range(1, 13):
            if datetime.datetime(year, month, NOW.day) <= NOW:
                url = SERVER + PATH.format(year, month)
                req = requests.head(url)

                # looks like some devs are not familiar with 404 status
                if req.headers.get('Content-Type') == 'application/x-download':
                    yield (url,year,month)

                else:
                    msg = 'Data from {:02d}/{} could not be located at: {}'
                    warnings.warn(msg.format(month, year, url))

def concat_csv_file(path_file):
    chunksize = 2000

    df = pandas.DataFrame(columns=COLLUNM_DATA)
    i=0
    j=0
    for df in pandas.read_csv(path_file, chunksize=chunksize, iterator=True,sep='\t',encoding='latin-1'):
         df = df.rename(columns={c: c.replace(' ', '') for c in df.columns})
         df.index += j
         i += 1
         if not os.path.isfile(BASE_DATA_DIR+'filename.csv'):
             df.to_csv(BASE_DATA_DIR+'filename.csv')
         else:  # else it exists so append without writing the header
             df.to_csv(BASE_DATA_DIR+'filename.csv', mode='a', header=False)
         j = df.index[-1] + 1



def download_datasets():
    os.makedirs(TEMP_DATA, exist_ok=True)
    for data in urls():
        url, year, month =  data
        print (url,year,month)
        filename = BASE_DATA_DIR +"file" +str(year) + str(month)+".zip"
        urlretrieve(url,filename,reporthook=dlProgress)
        zip_ref = zipfile.ZipFile(filename, 'r')
        print(zip_ref.namelist()[0])
        zip_ref.extractall(TEMP_DATA)
        concat_csv_file(TEMP_DATA+zip_ref.namelist()[0])
        zip_ref.close()



if __name__ == '__main__':
    download_datasets()
    shutil.rmtree(TEMP_DATA)

