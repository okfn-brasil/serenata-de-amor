import datetime
import os
import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


class CongresspersonDetails:

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_PATH = os.path.join(BASE_DIR, 'data')

    DATE = datetime.date.today().strftime('%Y-%m-%d')
    FILE_BASE_NAME = '{}-congressperson-details.xz'.format(DATE)

    CAMARA_URL = ('http://www.camara.leg.br/SitCamaraWS/Deputados.asmx/'
                  'ObterDetalhesDeputado?ideCadastro={}&numLegislatura=')

    CSV_PARAMS = {
        'compression': 'xz',
        'encoding': 'utf-8',
        'index': False
    }

    def __init__(self):
        self.total = 0

    def find_newest_file(self, name):

        date_regex = re.compile('\d{4}-\d{2}-\d{2}')

        matches = (date_regex.findall(f) for f in os.listdir(self.DATA_PATH))
        dates = sorted(set([l[0] for l in matches if l]), reverse=True)

        for date in dates:
            filename = '{}-{}.xz'.format(date, name)
            filepath = os.path.join(self.DATA_PATH, filename)

            if os.path.isfile(filepath):
                return filepath

        return None

    def read_csv(self, name):

        newest_file = self.find_newest_file(name)
        if newest_file is None:
            msg = 'Could not find the dataset for {}.'.format(newest_file)
            raise TypeError(msg)

        return pd.read_csv(newest_file, dtype={'congressperson_id': np.str})

    def get_all_congresspeople_ids(self):
        print('Fetching all congresspeople ids...')

        datasets = ('current-year', 'last-year', 'previous-years')
        ids = (self.read_csv(name)['congressperson_id'] for name in datasets)
        distinct_ids = pd.concat(ids).unique()
        self.total = len(distinct_ids)

        yield from (str(idx).strip() for idx in distinct_ids)

    def write_civil_file(self, congressperson_civil_names):
        df = pd.DataFrame(data=congressperson_civil_names)

        print('Writing file...')
        filepath = os.path.join(self.DATA_PATH, self.FILE_BASE_NAME)
        df.to_csv(filepath, **self.CSV_PARAMS)

        print('Done.')

    @staticmethod
    def parse_repository(data, congress_id):
        soup = BeautifulSoup(data, 'lxml')

        civil_name = soup.find('nomecivil').text

        birth_date = soup.find('datanascimento').text
        birth_date = datetime.datetime.strptime(birth_date, '%d/%m/%Y').date()

        gender = soup.find('sexo').text

        return {
            'congressperson_id': congress_id,
            'civil_name': civil_name,
            'birth_date': birth_date,
            'gender': gender.upper(),
        }

    def fetch_data_repository(self, congress_id):
        url = self.CAMARA_URL.format(congress_id)

        page = requests.get(url)

        if page.status_code != 200:
            msg = 'HTTP request to {} failed with status code {}'
            print(msg.format(url, page.status_code))
            return

        content = str(page.content.decode('utf-8'))

        return self.parse_repository(content, congress_id)

    def get_civil_names(self):
        congresspeople_ids = self.get_all_congresspeople_ids()
        for i, congress_id in enumerate(congresspeople_ids):
            if not np.math.isnan(float(congress_id)):
                percentage = (i / self.total * 100)
                msg = 'Processed {} out of {} ({:.2f}%)'
                print(msg.format(i, self.total, percentage), end='\r')

                data = self.fetch_data_repository(congress_id)

                if data is not None:
                    yield dict(data)


if __name__ == '__main__':
    details = CongresspersonDetails()
    details.write_civil_file(details.get_civil_names())
