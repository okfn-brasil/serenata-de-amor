from concurrent import futures
import configparser
import pickle
import os
import os.path
import pandas as pd
import re
import shutil
from suspectplacesearcher import SuspectPlaceSearch

DATASET_PATH = os.path.join('data', 'companies.xz')
TEMP_PATH = os.path.join('data', 'tmp_suspect_search')
CNPJ_REGEX = r'[./-]'

settings = configparser.RawConfigParser()
settings.read('config.ini')
sp = SuspectPlaceSearch(settings.get('Google', 'APIKey'))


def search_suspect_around_companies(companies):
    with futures.ThreadPoolExecutor(max_workers=40) as executor:
        future_to_search_suspects = dict()
        for index, company in companies.iterrows():
            future = executor.submit(search_suspect_around_company, company)
            future_to_search_suspects[future] = company
        for future in futures.as_completed(future_to_search_suspects):
            company = future_to_search_suspects[future]
            if future.exception() is not None:
                print('%r raised an exception: %s' % (company['cnpj'],
                                                      future.exception()))
            elif future.result() is not None:
                write_suspects_info(future.result(), company['cnpj'])


def search_suspect_around_company(company):

    latitude = company["latitude"]
    longitude = company['longitude']
    geolocation = "{},{}".format(latitude, longitude)
    if geolocation == '':
        print('No geolocation information for ', company[
              'name'], company['cnpj'],
              ' is impossible to search suspects around')
        return None
    else:
        try:
            suspect = sp.search(lat=latitude, lng=longitude)
        except ValueError as e:
            print(e)
            return None
        return suspect


def write_suspects_info(suspect_around, cnpj):
    cnpj = re.sub(CNPJ_REGEX, '', cnpj)
    print('Writing %s' % cnpj)
    with open('%s/%s.pkl' % (TEMP_PATH, cnpj), 'wb') as f:
        pickle.dump(suspect_around, f, pickle.HIGHEST_PROTOCOL)


def read_suspect_info(company):
    cnpj = re.sub(CNPJ_REGEX, '', company['cnpj'])
    filename = '%s/%s.pkl' % (TEMP_PATH, cnpj)
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            try:
                suspect_place = pickle.load(f)
            except (ValueError, EOFError) as e:
                return pd.Series()
        if suspect_place is None:
            return pd.Series()
        else:
            return pd.Series({'suspect_place_around': suspect_place['name'],
                              'distance_to_suspect': suspect_place['distance'],
                              'suspect_phone': suspect_place['phone'],
                              'suspect_latitude': suspect_place['latitude'],
                              'suspect_longitude': suspect_place['longitude'],
                              })
    else:
        return pd.Series()


if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)

data = pd.read_csv(DATASET_PATH, low_memory=False)

searched_for_suspects_cnpjs = [filename[:14]
                               for filename in os.listdir(TEMP_PATH)
                               if filename.endswith('.pkl')]

is_not_searched_for_suspects = ~data['cnpj'].str.replace(
    CNPJ_REGEX, '').isin(searched_for_suspects_cnpjs)

remaining_companies = data[is_not_searched_for_suspects]

print('%i companies, %i to go' % (len(data), len(remaining_companies)))

search_suspect_around_companies(remaining_companies)

data = pd.concat([data,
                  data.apply(read_suspect_info, axis=1)], axis=1)

data.to_csv(DATASET_PATH,
            compression='xz',
            encoding='utf-8',
            index=False)

shutil.rmtree(TEMP_PATH)
