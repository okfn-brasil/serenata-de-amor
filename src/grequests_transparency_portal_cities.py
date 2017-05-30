import os
import unicodedata

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
         return 404
    return response.status_code


def format_url(row, url):
    if row['status_code'] != 200:
        return url.format(row['normalized_name'], row['state'].lower())
    return row['transparency_portal_url']


def check_transparency_portal_existance(dataset, portal_urls):
    dataset['transparency_portal_url'] = 'None'
    dataset['status_code'] = 0

    for url in portal_urls:
        dataset['transparency_portal_url'] = dataset.apply(format_url, axis=1, args=(url,))
        rs = (grequests.get(u) for u \
              in list(dataset.loc[dataset['status_code'] != 200, 'transparency_portal_url']))

        responses = grequests.map(rs, exception_handler=exception_handler)
        responses = [get_status_code(r) for r in responses]

        dataset.loc[dataset['status_code'] != 200, 'status_code'] = responses
        dataset.loc[dataset['status_code'] != 200, 'transparency_portal_url'] = 'None'


def main(data_path='/tmp/serenata-data', cities_file='2017-05-22-brazilian-cities.csv'):
    Datasets(data_path).downloader.download(cities_file)
    cities = pd.read_csv(os.path.join(data_path, cities_file))

    cities['normalized_name'] = cities['name'].apply(normalize_string)

    portal_urls = ['https://{}-{}.portaltp.com.br/',
                  'https://cm{}-{}.portaltp.com.br/']
    check_transparency_portal_existance(cities, portal_urls)

    unnecessary_columns = ['normalized_name', 'status_code']
    cities = cities.drop(unnecessary_columns, axis=1)

    cities.to_csv(os.path.join(data_path, 'cities-with-tp-url.xz'),
                     compression='xz', index=False)


if __name__ == '__main__':
    main()
