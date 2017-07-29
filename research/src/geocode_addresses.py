from concurrent import futures
import configparser
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut
import pickle
import os
import os.path
import pandas as pd
import re
import shutil

DATASET_PATH = os.path.join('data', 'companies.xz')
TEMP_PATH = os.path.join('data', 'companies')
CNPJ_REGEX = r'[./-]'

settings = configparser.RawConfigParser()
settings.read('config.ini')
geolocator = GoogleV3(settings.get('Google', 'APIKey'))

def geocode_companies(companies):
    with futures.ThreadPoolExecutor(max_workers=40) as executor:
        future_to_geocoding = dict()
        for index, company in companies.iterrows():
            future = executor.submit(geocode_company, company)
            future_to_geocoding[future] = company
        for future in futures.as_completed(future_to_geocoding):
            company = future_to_geocoding[future]
            if future.exception() is not None:
                print('%r raised an exception: %s' % (company['cnpj'],
                                                      future.exception()))
            elif future.result() is not None:
                write_geocoding_info(future.result(), company['cnpj'])
        companies.apply(geocode_company, axis=1)

def geocode_company(company):
    address = ' '.join(company[['address',
                                'number',
                                'zip_code',
                                'neighborhood',
                                'city',
                                'state']].dropna())
    if address == '':
        print('No address information for', company['name'], company['cnpj'])
        return None
    else:
        try:
            location = geolocator.geocode(address)
        except GeocoderTimedOut as e:
            print('Timeout')
            return None
        return location

def write_geocoding_info(company_location, cnpj):
    cnpj = re.sub(CNPJ_REGEX, '', cnpj)
    print('Writing %s' % cnpj)
    with open('%s/%s.pkl' % (TEMP_PATH, cnpj), 'wb') as f:
        pickle.dump(company_location, f, pickle.HIGHEST_PROTOCOL)

def read_geocoding_info(company):
    cnpj = re.sub(CNPJ_REGEX, '', company['cnpj'])
    filename = '%s/%s.pkl' % (TEMP_PATH, cnpj)
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            try:
                location = pickle.load(f)
            except (ValueError, EOFError) as e:
                return pd.Series()
        if location is None:
            return pd.Series()
        else:
            return pd.Series({'latitude': location.latitude,
                              'longitude': location.longitude})
    else:
        return pd.Series()



if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)

data = pd.read_csv(DATASET_PATH, low_memory=False)
geocoded_cnpjs = [filename[:14]
                  for filename in os.listdir(TEMP_PATH)
                  if filename.endswith('.pkl')]
is_not_geocoded = ~data['cnpj'].str.replace(CNPJ_REGEX, '').isin(geocoded_cnpjs)
remaining_companies = data[is_not_geocoded]
print('%i companies, %i to go' % (len(data), len(remaining_companies)))
geocode_companies(remaining_companies)
data = pd.concat([data,
                  data.apply(read_geocoding_info, axis=1)], axis=1)
data.to_csv(DATASET_PATH,
            compression='xz',
            encoding='utf-8',
            index=False)
shutil.rmtree(TEMP_PATH)
