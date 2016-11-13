import datetime
import os
import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


DATA_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(DATA_BASE_DIR, 'data')
DATE = datetime.date.today().strftime('%Y-%m-%d')
FILE_BASE_NAME = '{}-congressperson-civil-names.xz'.format(DATE)
URL_SCRAPING = 'http://www.camara.leg.br/Internet/deputado/Dep_Detalhe.asp?id={}'

CSV_PARAMS = {
    'compression': 'xz',
    'encoding': 'utf-8',
    'index': False
}


def find_newest_file(name):

    date_regex = re.compile('\d{4}-\d{2}-\d{2}')

    matches = (date_regex.findall(f) for f in os.listdir(DATA_PATH))
    dates = sorted(set([l[0] for l in matches if l]), reverse=True)

    for date in dates:
        filename = os.path.join(DATA_PATH, '{}-{}.xz'.format(date, name))

        if os.path.isfile(filename):
            return filename

    return None


def read_csv(name):

    newest_file = find_newest_file(name)
    if newest_file is None:
        raise TypeError('Could not find the dataset for {%s}.' % newest_file)

    return pd.read_csv(newest_file, dtype={
                                        'congressperson_id': np.str
                                    })


def get_all_congress_people_ids():
    print('Fetching all congress people ids...')

    ids = (read_csv(name)['congressperson_id'] for name in ['current-year', 'last-year', 'previous-years'])
    return list(str(idx).replace('\n', '').strip() for idx in pd.concat(ids).unique())


def write_civil_file(congressperson_civil_names):
    print('Writing file...')
    df = pd.DataFrame(data=congressperson_civil_names)
    df.to_csv(os.path.join(DATA_PATH, FILE_BASE_NAME), **CSV_PARAMS)

    print('Done.')


def get_civil_names():

    congress_people_ids = get_all_congress_people_ids()
    total = len(congress_people_ids)
    congress_civil_name = []

    for ind, congress_id in enumerate(congress_people_ids):

        page = requests.get(URL_SCRAPING.format(congress_id))
        data = str(page.content.decode('utf-8'))

        if page.status_code != 200:
            raise TypeError('could not request')

        try:
            parliamentary = {}

            soup = BeautifulSoup(data, 'html.parser')
            attributes = soup.findAll('ul', attrs={'class': 'visualNoMarker'})[0]
            line_name = attributes.find('li')

            # extract tag strong from line_name
            [x.extract() for x in line_name('strong')]

            parliamentary['congressperson_id'] = congress_id
            parliamentary['civil_name'] = line_name.text.strip()

            congress_civil_name.append(parliamentary)

            print('Processed {} out of {} ({:.2f}%)'.format(ind, total, ind / total * 100))
        except IndexError:
            print('Could not parse data')

    write_civil_file(congress_civil_name)

if __name__ == '__main__':
    get_civil_names()
