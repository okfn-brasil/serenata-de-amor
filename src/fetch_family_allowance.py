import datetime
import warnings
import sys
import requests
import zipfile
from urllib.request import urlretrieve
import os
import pandas
import tempfile
import shutil


STARTING_YEAR = 2016

NOW = datetime.datetime.now()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMP_DATA = os.path.join(BASE_DIR, BASE_DATA_DIR, 'temp_data')
SERVER = 'http://arquivos.portaldatransparencia.gov.br/'
PATH = 'downloads.asp?a={}&m={:02d}&consulta=BolsaFamiliaFolhaPagamento'
OUTPUTFILE = os.path.join(BASE_DATA_DIR, '{}-family_allowance.xz')
OUTPUTFILETEMP = 'Temp_file_family_allowance{}{}.zip'

CSV_PARAMS = {
    'compression': 'xz',
    'encoding': 'utf-8',
    'index': False
}

COLUMNS = {'UF': 'FEDERAL_UNIT',
           'CódigoSIAFIMunicípio': 'CODE_SIAFI_TONW',
           'NomeMunicípio': 'TOWN_NAME',
           'CódigoFunção': 'FUNCTION_CODE',
           'CódigoSubfunção': 'SUBFUNCTION_CODE',
           'CódigoPrograma': 'PROGRAM_CODE',
           'CódigoAção': 'ACTION_CODE',
           'NISFavorecido': 'FAVORED_NIS',
           'NomeFavorecido': 'FAVORED_NAME',
           'Fonte-Finalidade': 'SOURCE_FINALITY',
           'ValorParcela': 'PARCEL_VALUE',
           'MêsCompetência': 'MONTH_COMPETENCE',
           }


def dlProgress(count, blockSize, totalSize):
    print("….........", end='\r')
    sys.stdout.flush()


def urls():
    for year in range(STARTING_YEAR, NOW.year + 1):
        for month in range(1, 13):
            if datetime.datetime(year, month, NOW.day) <= NOW:
                url = SERVER + PATH.format(year, month)
                req = requests.head(url)
                if req.headers.get('Content-Type') == 'application/x-download':
                    yield (url, year, month)
                else:
                    msg = 'Data from {:02d}/{} could not be located at: {}'
                    warnings.warn(msg.format(month, year, url))


def translate_conlumns_and_save_csvs_files_family_allowance(path_file):
    chunksize = 50000000
    df = pandas.DataFrame()
    for df in pandas.read_csv(
            path_file,
            chunksize=chunksize,
            iterator=True,
            sep='\t',
            encoding='latin-1'):

        df = df.rename(columns={c: c.replace(' ', '') for c in df.columns})
        df.rename(columns=COLUMNS, inplace=True)
        if not os.path.isfile(OUTPUTFILE.format(
                str(NOW.year), str(NOW.month), str(NOW.day))):
            print('Writing file...')
            df.to_csv(df.to_csv(OUTPUTFILE.format(
                datetime.datetime.today().strftime('%Y-%m-%d')), **CSV_PARAMS))

        else:  # else it exists so append without writing the header
            print('Writing file...')
            df.to_csv(OUTPUTFILE.format(datetime.datetime.today().strftime(
                '%Y-%m-%d')), mode='a', header=False, **CSV_PARAMS)


def download_datasets():
    for data in urls():
        url, year, month = data
        print(url, year, month)
        tmpdir = tempfile.mkdtemp()
        print(tmpdir)
        os.path.dirname(os.path.dirname(os.path.abspath(tmpdir)))
        filename = tmpdir + OUTPUTFILETEMP.format(str(year), str(month))
        print(filename)
        print(os.path.abspath(tmpdir))
        urlretrieve(url, filename, reporthook=dlProgress)
        zip_ref = zipfile.ZipFile(filename, 'r')
        print(zip_ref.namelist()[0])
        zip_ref.extractall(tmpdir)
        temppath = os.path.join(tmpdir, zip_ref.namelist()[0])
        translate_conlumns_and_save_csvs_files_family_allowance(temppath)
        zip_ref.close()
    shutil.rmtree(tmpdir)


if __name__ == '__main__':
    download_datasets()
