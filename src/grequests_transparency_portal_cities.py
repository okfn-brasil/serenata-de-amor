import os
import unicodedata

import pandas as pd
import grequests

from serenata_toolbox.datasets import Datasets

def normalize_string(string):
    if isinstance(string, str):
        nfkd_form = unicodedata.normalize('NFKD', string.lower())
        return nfkd_form.encode('ASCII', 'ignore').decode('utf-8')


def exception_handler(request, exception):
    return type('Response', (object,), {'status_code': None})

def get_status_code(response):
    if not response.status_code:
         return 404
    return response.status_code

def main(data_path='/tmp/serenata-data', cities_file='2017-05-22-brazilian-cities.csv'):
    Datasets(data_path).downloader.download(cities_file)
    br_cities = pd.read_csv(os.path.join(data_path, cities_file))

    br_cities['state'] = br_cities['state'].apply(str.lower)

    br_cities['normalized_name'] = br_cities['name'] \
                                              .apply(lambda x: normalize_string(x))
    br_cities['normalized_name'] = br_cities['normalized_name'] \
                                               .apply(lambda x: x.replace(' ', ''))

    portal_url = 'https://{}-{}.portaltp.com.br/'
    br_cities['transparency_portal_url'] = br_cities \
            .apply(lambda row: portal_url.format(row['normalized_name'],
                                                 row['state']), axis=1)

    rs = (grequests.get(u) for u in list(br_cities['transparency_portal_url']))

    responses = grequests.map(rs, exception_handler=exception_handler)

    br_cities.loc[:,'status_code'] = responses

    br_cities.loc[:,'status_code'] = br_cities \
            .apply(lambda row: get_status_code(row['status_code']), axis=1)

    br_cities.loc[br_cities['status_code'] == 404, 'transparency_portal_url'] = None

    portal_url = 'https://cm{}-{}.portaltp.com.br/'
    br_cities_cm = br_cities[br_cities['status_code'] == 404]

    br_cities_cm.loc[:,'transparency_portal_url'] = br_cities_cm \
            .apply(lambda row: portal_url.format(row['normalized_name'],
                                                 row['state']), axis=1)

    rs = (grequests.get(u) for u in list(br_cities_cm['transparency_portal_url']))

    responses = grequests.map(rs, exception_handler=exception_handler)

    br_cities_cm.loc[:,'status_code'] = responses

    br_cities_cm.loc[:,'status_code'] = br_cities_cm \
            .apply(lambda row: get_status_code(row['status_code']), axis=1)
    br_cities_cm.loc[br_cities_cm['status_code'] == 404, 'transparency_portal_url'] = None

    unnecessary_columns = ['normalized_name', 'status_code']
    br_cities = pd.merge(br_cities.drop(unnecessary_columns, axis=1),
		                 br_cities_cm.drop(unnecessary_columns, axis=1),
		                 on=['code', 'name', 'state'], how='left')

    br_cities['transparency_portal_url'] = br_cities \
	  .apply(lambda row: row['transparency_portal_url_x'] or row['transparency_portal_url_y'], axis=1)

    unnecessary_columns = ['transparency_portal_url_x', 'transparency_portal_url_y']
    br_cities = br_cities.drop(unnecessary_columns, axis=1)
    br_cities['state'] = br_cities['state'].apply(str.upper)

    br_cities.to_csv(os.path.join(data_path, 'cities-with-tp-url.xz'),
                     compression='xz', index=False)


if __name__ == '__main__':
    main()
