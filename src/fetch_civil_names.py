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
    URL_SCRAPING = 'http://www.camara.leg.br/Internet/deputado/Dep_Detalhe.asp?id={}'

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

    def get_civil_names(self):

        congresspeople_ids = self.get_all_congresspeople_ids()
        for ind, congress_id in enumerate(congresspeople_ids):

            page = requests.get(self.URL_SCRAPING.format(congress_id))
            data = str(page.content.decode('utf-8'))

            if page.status_code != 200:
                msg = 'HTTP request to {} failed with status code {}'
                print(msg.format(self.URL_SCRAPING.format(congress_id), page.status_code))

            try:
                soup = BeautifulSoup(data, 'html.parser')
                attributes = soup.findAll('ul', attrs={'class': 'visualNoMarker'})[0]
                line_name = attributes.find('li')

                # extract tag strong from line_name
                [x.extract() for x in line_name('strong')]

                print('Processed {} out of {} ({:.2f}%)'.format(ind, self.total, ind / self.total * 100))

                yield dict(congressperson_id=congress_id, civil_name=line_name.text.strip())
            except IndexError:
                print('Could not parse data')

if __name__ == '__main__':
    civil_names = CivilNames()
    civil_names.write_civil_file(civil_names.get_civil_names())

