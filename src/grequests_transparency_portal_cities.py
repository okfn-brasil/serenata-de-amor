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


def format_row(row, url):
    if row['transparency_portal_url'] == 'None':
        return url.format(row['normalized_name'], row['state'].lower())
    return row['transparency_portal_url']


def check_transparency_portal_existance(dataset, portal_urls):
    dataset['transparency_portal_url'] = 'None'

    for url in portal_urls:
        dataset['transparency_portal_url'] = dataset.apply(format_row, axis=1, args=(url,))
        # TODO: Also filter by status_code
        rs = (grequests.get(u) for u in list(dataset['transparency_portal_url']))
        responses = grequests.map(rs, exception_handler=exception_handler)
        dataset.loc[:,'status_code'] = responses
        dataset.loc[:,'status_code'] = dataset \
               .apply(lambda row: get_status_code(row['status_code']), axis=1)
        dataset.loc[dataset['status_code'] == 404, 'transparency_portal_url'] = 'None'


def main(data_path='/tmp/serenata-data', cities_file='2017-05-22-brazilian-cities.csv'):
    Datasets(data_path).downloader.download(cities_file)
    cities = pd.read_csv(os.path.join(data_path, cities_file))
    cities = cities.head(50).copy()

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
