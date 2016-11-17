import datetime
import html
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
            filename = os.path.join(self.DATA_PATH, '{}-{}.xz'.format(date, name))

            if os.path.isfile(filename):
                return filename

        return None

    def read_csv(self, name):

        newest_file = self.find_newest_file(name)
        if newest_file is None:
            raise TypeError('Could not find the dataset for {%s}.' % newest_file)

        return pd.read_csv(newest_file, dtype={
                                            'congressperson_id': np.str
                                        })

    def get_all_congresspeople_ids(self):
        print('Fetching all congresspeople ids...')

        ids = (self.read_csv(name)['congressperson_id'] for name in ['current-year', 'last-year', 'previous-years'])
        distinct_ids = pd.concat(ids).unique()
        self.total = len(distinct_ids)

        yield from (str(idx).strip() for idx in distinct_ids)

    def write_civil_file(self, congressperson_civil_names):
        df = pd.DataFrame(data=congressperson_civil_names)

        print('Writing file...')
        df.to_csv(os.path.join(self.DATA_PATH, self.FILE_BASE_NAME), **self.CSV_PARAMS)

        print('Done.')

    def fetch_primary_repository(self, congress_id):
        page = requests.get(self.PRIMARY_URL.format(congress_id))
        data = str(page.content.decode('utf-8'))

        if page.status_code != 200:
            msg = 'HTTP request to {} failed with status code {}'
            print(msg.format(self.PRIMARY_URL.format(congress_id), page.status_code))

            try:
                soup = BeautifulSoup(data, 'html.parser')
                attributes = soup.findAll('ul', attrs={'class': 'visualNoMarker'})[0]
                line_name = attributes.find('li')

                # extract tag strong from line_name
                [x.extract() for x in line_name('strong')]

                return dict(congressperson_id=congress_id, civil_name=str(line_name.text.strip()).upper())
            except IndexError:
                print('Could not parse data')

        return None

    def fetch_secondary_repository(self, congress_id):
        page = requests.get(self.SECONDARY_URL.format(congress_id))
        data = str(page.content.decode('utf-8'))

        if page.status_code != 200:
            msg = 'HTTP request to {} failed with status code {}'
            print(msg.format(self.SECONDARY_URL.format(congress_id), page.status_code))

        try:
            soup = BeautifulSoup(data, 'html.parser')
            attributes = soup.findAll('div', attrs={'class': 'bioDetalhes'})[0]
            line_name = attributes.find('strong')

            return dict(congressperson_id=congress_id, civil_name=str(line_name.text.strip()).upper())
        except IndexError:
            print('Could not parse data')

    def fetch_data_repository(self, congress_id):

        data = self.fetch_primary_repository(congress_id)

        if data is None:
            return self.fetch_secondary_repository(congress_id)
        else:
            return data

    def get_civil_names(self):

        congresspeople_ids = self.get_all_congresspeople_ids()
        for ind, congress_id in enumerate(congresspeople_ids):

            if not np.math.isnan(float(congress_id)):
                print('Processed {} out of {} ({:.2f}%)'.format(ind, self.total, ind / self.total * 100))
                yield dict(self.fetch_data_repository(congress_id))

if __name__ == '__main__':
    civil_names = CivilNames()
    civil_names.write_civil_file(civil_names.get_civil_names())

