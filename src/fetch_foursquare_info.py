import configparser
import datetime
import numpy as np
import os.path
import pandas as pd
import re
import requests
from pandas.io.json import json_normalize

DATA_DIR = 'data'
DATE = datetime.date.today().strftime('%Y-%m-%d')


def find_newest_file(name):
    """
    Assuming that the files will be in the form of :
    yyyy-mm-dd-type_of_file.xz we can try to find the newest file
    based on the date, but if the file doesn't exist fallback to another
    date until all dates are exhausted
    """
    date_regex = re.compile('\d{4}-\d{2}-\d{2}')

    matches = (date_regex.findall(f) for f in os.listdir(DATA_DIR))
    dates = sorted(set([l[0] for l in matches if l]), reverse=True)
    for date in dates:
        filename = os.path.join(DATA_DIR, '{}-{}.xz'.format(date, name))
        if os.path.isfile(filename):
            return filename
    return None


def load_cnpjs(subquota_description):
    """Return a list of CNPJs from the given subquota_description"""
    u_cols = ['cnpj_cpf', 'subquota_description']
    docs = pd.read_csv(REIMBURSEMENTS_DATASET_PATH,
                       low_memory=False,
                       usecols=u_cols,
                       dtype={'cnpj_cpf': np.str})
    meals = docs[docs.subquota_description == subquota_description]
    return meals['cnpj_cpf'].unique()


def only_numbers(string):
    """Return a string w only the numbers from the given string"""
    return re.sub("\D", "", string)


def load_companies_dataset(cnpjs):
    """Return a DataFrame of companies from the given list of cnpjs"""
    u_cols = ['cnpj', 'trade_name', 'zip_code', 'latitude', 'longitude']
    all_companies = pd.read_csv(COMPANIES_DATASET_PATH,
                                low_memory=False,
                                usecols=u_cols,
                                dtype={'trade_name': np.str})
    all_companies = all_companies.dropna(subset=['cnpj', 'trade_name'])
    all_companies['clean_cnpj'] = all_companies['cnpj'].map(only_numbers)
    return all_companies[all_companies['clean_cnpj'].isin(cnpjs)]


def remaining_companies(companies, fetched_companies):
    """Return the first DF but without matching CNPJs from the second DF"""
    remaining = companies[~companies['cnpj'].isin(fetched_companies['cnpj'])]
    return remaining.reset_index()


def load_foursquare_companies_dataset():
    """Return a DF with the data already collected. Fallback to empty one"""

    if FOURSQUARE_DATASET_PATH is not None:
        return pd.read_csv(FOURSQUARE_DATASET_PATH)
    return pd.DataFrame(columns=['cnpj'])


def get_venue(company):
    """Return a matching venue from Foursquare for the given company Series"""
    venue = search(company)
    if venue:
        return fetch_venue(venue['id'])


def search(company):
    """Search Foursquare's API for a match for a given company Series"""
    params = dict(DEFAULT_PARAMS)

    params.update({'query': company['trade_name'],
                   'll': '%s,%s' % (company['latitude'], company['longitude']),
                   'zip_code': company['zip_code'],
                   'intent': 'match'})

    url = 'https://api.foursquare.com/v2/venues/search'
    response = requests.get(url, params=params)
    result = parse_search_results(response, True)

    if not result:
        params.pop('intent')
        response = requests.get(url, params=params)
        result = parse_search_results(response, False)

    return result


def parse_search_results(response, confirmed_match):
    """Return the first venue from the given search response"""
    json_response = response.json()
    venues = json_response.get('response', {}).get('venues')
    if venues:
        venue = venues[0]
        venue['confirmed_match'] = confirmed_match
        return venue


def fetch_venue(venue_id):
    """Return specific data from Foursquare for the given venue_id"""
    url = 'https://api.foursquare.com/v2/venues/%s' % venue_id
    response = requests.get(url, params=DEFAULT_PARAMS)
    return parse_venue_info(response)


def parse_venue_info(response):
    """Return only venue data from the given fetch_venue response"""
    json_response = response.json()
    venue = json_response.get('response', {}).get('venue')
    return venue


def write_fetched_companies(companies):
    """Save a compressed CSV file with the given DF"""
    companies.to_csv(OUTPUT_DATASET_PATH,
                     compression='xz',
                     index=False)

# API Keys
# You can create your own through https://pt.foursquare.com/developers/register
settings = configparser.RawConfigParser()
settings.read('config.ini')
CLIENT_ID = settings.get('Foursquare', 'ClientId')
CLIENT_SECRET = settings.get('Foursquare', 'ClientSecret')
# Foursquare API Version. This is in YYYYMMDD format.
VERSION = '20161021'
# Required params to make a request to Foursquare's API
DEFAULT_PARAMS = {'client_id': CLIENT_ID,
                  'client_secret': CLIENT_SECRET,
                  'v': VERSION}

# Dataset paths
REIMBURSEMENTS_DATASET_PATH = find_newest_file('reimbursements')
COMPANIES_DATASET_PATH = find_newest_file('companies')
FOURSQUARE_DATASET_PATH = find_newest_file('foursquare-companies')
OUTPUT_DATASET = '{}-foursquare-companies.xz'.format(DATE)
OUTPUT_DATASET_PATH = os.path.join(DATA_DIR, OUTPUT_DATASET)

if __name__ == '__main__':
    if not (CLIENT_ID and CLIENT_SECRET):
        raise 'Missing API credentials'

    meal_cnpjs = load_cnpjs('Congressperson meal')
    meal_companies = load_companies_dataset(meal_cnpjs)
    fetched_companies = load_foursquare_companies_dataset()
    remaining_companies = remaining_companies(meal_companies, fetched_companies)

    for index, company in remaining_companies.iterrows():
        print('Looking for: %s' % company['trade_name'])
        fetched = get_venue(company)
        if fetched:
            print('Was found  : %s! <=======<<<' % fetched['name'])
            fetched['trade_name'] = company['trade_name']
            fetched['cnpj'] = company['cnpj']
            fetched['clean_cnpj'] = company['clean_cnpj']
            fetched['scraped_at'] = datetime.datetime.utcnow().isoformat()
            fetched = json_normalize(fetched)

            fetched_companies = pd.concat([fetched_companies, fetched])
        else:
            print('No results.')

        if (index % 100) == 0 and index > 0:
            print('###########################################')
            print("%s companies fetched. Stopping to save." % index)
            write_fetched_companies(fetched_companies)
            print('###########################################')
    write_fetched_companies(fetched_companies)
