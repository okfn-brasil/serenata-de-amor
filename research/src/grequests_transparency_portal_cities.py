import os
import unicodedata
from argparse import ArgumentParser
from datetime import date

import grequests
import numpy as np
import pandas as pd

from serenata_toolbox.datasets import Datasets


def normalize_string(string):
    if isinstance(string, str):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8').replace(' ', '')


def exception_handler(request, exception):
    return type('Response', (object,), {'status_code': None})


def get_status_code(response):
    if not response.status_code:
         return 0
    return response.status_code


def format_url(row, url):
    if row['status_code'] == 0:
        return url.format(row['normalized_name'], row['state'].lower())
    return row['transparency_portal_url']


def check_transparency_portal_existance(dataset, portal_urls):
    dataset['transparency_portal_url'] = 'None'
    dataset['status_code'] = 0

    for url in portal_urls:
        dataset['transparency_portal_url'] = dataset.apply(format_url, axis=1, args=(url,))
        rs = (grequests.head(u) for u \
              in list(dataset.loc[dataset['status_code'] == 0, 'transparency_portal_url']))

        responses = grequests.map(rs, exception_handler=exception_handler)
        responses = [get_status_code(r) for r in responses]

        dataset.loc[dataset['status_code'] == 0, 'status_code'] = responses
        dataset.loc[dataset['status_code'] == 0, 'transparency_portal_url'] = 'None'


def save_csv(dataset, data_path):
    dataset_name = '{}-{}'.format(date.today().strftime('%Y-%m-%d'), 'cities-with-tp-url.xz')
    dataset_path = os.path.join(data_path, dataset_name)
    dataset.to_csv(dataset_path, compression='xz', encoding='utf-8', index=False)


def main(data_path, cities_file):
    cities = pd.read_csv(os.path.join(data_path, cities_file))

    cities['normalized_name'] = cities['name'].apply(normalize_string)

    portal_urls = ['https://{}-{}.portaltp.com.br/',
                  'https://cm{}-{}.portaltp.com.br/']
    check_transparency_portal_existance(cities, portal_urls)

    cities = cities.drop('normalized_name', axis=1)
    save_csv(cities, data_path)


if __name__ == '__main__':
    description = """
    This script generates a CSV file containing all the Brazilian
    cities and the URLs for their transparency portal if a transparency portal
    exists
    """

    parser = ArgumentParser(description=description)
    parser.add_argument(
        '--cities-file', '-c', default='2017-05-22-brazilian-cities.csv',
        help=('A CSV file containing all Brazilian cities per state '
              '(default: 2017-05-22-brazilian-cities.csv)')
    )
    parser.add_argument(
        '--data-dir', '-d', default='data/',
        help=('Data directory where Brazilian cities .csv file can be found '
              '(default: data/)')
    )
    args = parser.parse_args()

    if not os.path.exists(os.path.join(args.data_dir, args.cities_file)):
        Datasets(args.data_dir).downloader.download(args.cities_file)

    main(
        args.data_dir,
        args.cities_file
    )
