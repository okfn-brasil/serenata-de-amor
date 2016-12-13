import os
import zipfile
import pandas as pd
import numpy as np
from urllib.request import urlretrieve

def download_source():
    datasets_urls = [
        'http://portal.convenios.gov.br/images/docs/CGSIS/csv/siconv_emenda.csv.zip']
    filenames = map(lambda url: url.split('/')[-1], datasets_urls)
    datasets_names = [
        'amendments.xz']

    for url, filename, dataset_name in zip(datasets_urls, filenames, datasets_names):
        filepath = 'data/%s' % filename
        print('Downloading %s' % filename)
        urlretrieve(url, filepath)
        zip_ref = zipfile.ZipFile(filepath, 'r')
        zip_ref.extractall('data')
        zip_ref.close()

        print('Renaming columns in: %s' % filepath.replace('.zip', ''))
        data = pd.read_csv(filepath_or_buffer=filepath.replace('.zip', ''), sep=';')
        data.rename(columns={
                'ID_PROPOSTA':'proposal_id',
                'QUALIF_PROPONENTE':'proponent_qualification',
                'COD_PROGRAMA_EMENDA':'amendment_program_code',
                'NR_EMENDA':'amendment_number',
                'NOME_PARLAMENTAR':'congressperson_name',
                'BENEFICIARIO_EMENDA':'amendment_beneficiary',
                'IND_IMPOSITIVO':'tax_indicative',
                'TIPO_PARLAMENTAR':'congressperson_type',
                'VALOR_REPASSE_PROPOSTA_EMENDA':'amendment_proposal_tranfer_value',
                'VALOR_REPASSE_EMENDA':'amendment_tranfer_value'
            }, inplace=True)

        print('Saving %s dataset' % dataset_name)
        data.to_csv(path_or_buf='data/%s' % dataset_name, sep=',', compression='xz', index=False)

        print('Removing temporary files')
        os.remove(filepath)
        os.remove(filepath.replace('.zip', ''))

download_source()
