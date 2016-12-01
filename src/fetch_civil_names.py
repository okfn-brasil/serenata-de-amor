import datetime
import os
import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


class CivilNames:

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_PATH = os.path.join(BASE_DIR, 'data')

    DATE = datetime.date.today().strftime('%Y-%m-%d')
    FILE_BASE_NAME = '{}-congressperson-civil-names.xz'.format(DATE)

    PRIMARY_URL = 'http://www.camara.leg.br/Internet/deputado/Dep_Detalhe.asp?id={}'
    SECONDARY_URL = 'http://www2.camara.leg.br/deputados/pesquisa/layouts_deputados_biografia?pk={}'

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
    def parse_primary_repository(data, congress_id):
        try:
            soup = BeautifulSoup(data, 'html.parser')
            attrs = {'class': 'visualNoMarker'}
            attributes = soup.findAll('ul', attrs=attrs)[0]
            line_name = attributes.find('li')
            [x.extract() for x in line_name('strong')]  # extract tag strong
            civil_name = str(line_name.text.strip()).upper()

            return dict(congressperson_id=congress_id, civil_name=civil_name)

        except IndexError:
            print('Could not parse data')

    @staticmethod
    def parse_secondary_repository(data, congress_id):
        try:
            soup = BeautifulSoup(data, 'html.parser')
            attributes = soup.findAll('div', attrs={'class': 'bioDetalhes'})[0]
            line_name = attributes.find('strong')
            civil_name = str(line_name.text.strip()).upper()
            return dict(congressperson_id=congress_id, civil_name=civil_name)

        except IndexError:
            print('Could not parse data')

    @staticmethod
    def fetch_repository(url, congressperson_id, parser):
        page = requests.get(url)

        if page.status_code != 200:
            msg = 'HTTP request to {} failed with status code {}'
            print(msg.format(url, page.status_code))
            return

        data = str(page.content.decode('utf-8'))
        return parser(data, congressperson_id)

    def fetch_data_repository(self, congress_id):
        primary_url = self.PRIMARY_URL.format(congress_id)
        data = self.fetch_repository(
            primary_url,
            congress_id,
            self.parse_primary_repository
        )

        if not data:
            secondary_url = self.SECONDARY_URL.format(congress_id)
            return self.fetch_repository(
                secondary_url,
                congress_id,
                self.parse_secondary_repository
            )
        return data

    def get_civil_names(self):
        congresspeople_ids = self.get_all_congresspeople_ids()
        for ind, congress_id in enumerate(congresspeople_ids):
            if not np.math.isnan(float(congress_id)):
                percentage = (ind / self.total * 100)
                msg = 'Processed {} out of {} ({:.2f}%)'
                print(msg.format(ind, self.total, percentage), end='\r')
                yield dict(self.fetch_data_repository(congress_id))

if __name__ == '__main__':
    civil_names = CivilNames()
    civil_names.write_civil_file(civil_names.get_civil_names())
