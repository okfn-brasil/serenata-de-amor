import configparser
import datetime
import json
import numpy as np
import os.path
import pandas as pd
import re
import requests
from pandas.io.json import json_normalize

# Dataset paths
REIMBURSEMENTS_DATASET_PATH = os.path.join('data', '2016-11-22-reimbursements.xz')
COMPANIES_DATASET_PATH = os.path.join('data', '2016-09-03-companies.xz')
FOURSQUARE_DATASET_PATH = os.path.join('data', 'foursquare-companies.xz')

# API Keys
# You can create your own through https://pt.foursquare.com/developers/register
settings = configparser.RawConfigParser()
settings.read('config.ini')
CLIENT_ID = settings.get('Foursquare', 'ClientId')
CLIENT_SECRET = settings.get('Foursquare', 'ClientSecret')
#Foursquare API Version. This is in YYYYMMDD format.
VERSION = '20161021'

# Required params to make a request to Foursquare's API
DEFAULT_PARAMS = {'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'v': VERSION}

def load_cnpjs(subquota_description):
    """Return a list of CNPJs from the given subquota_description"""
    u_cols = ['cnpj_cpf', 'subquota_description']
    docs = pd.read_csv(REIMBURSEMENTS_DATASET_PATH,
                        low_memory=False,
                        usecols=u_cols,
                        dtype={'cnpj_cpf': np.str})
    meals = docs[docs.subquota_description == subquota_description]
    return meals['cnpj_cpf'].unique()

def load_companies_dataset(cnpjs):
    """Return a DataFrame of companies from the given list of cnpjs"""
    u_cols = ['cnpj', 'trade_name', 'zip_code', 'latitude', 'longitude']
    all_companies = pd.read_csv(COMPANIES_DATASET_PATH,
                                low_memory=False,
                                usecols=u_cols,
                                dtype={'trade_name': np.str})
    all_companies['clean_cnpj'] = all_companies['cnpj'].map(only_numbers)
    return all_companies[all_companies['clean_cnpj'].isin(cnpjs)]

def only_numbers(string):
    """Return a string w only the numbers from the given string"""
    return re.sub("\D", "", string)

def remaining_companies(companies, fetched_companies):
    """Return the first DF but without matching CNPJs from the second DF"""
    return companies[~companies['cnpj'].isin(fetched_companies['cnpj'])]

def load_foursquare_companies_dataset():
    """Return a DF with the data already collected"""
    if os.path.exists(FOURSQUARE_DATASET_PATH):
        return pd.read_csv(FOURSQUARE_DATASET_PATH)
    else:
        return pd.DataFrame(columns=['cnpj'])

def get_venue(company):
    """Return a matching venue from Foursquare for the given company Series"""
    venue = search(company)
    if venue:
        return fetch_venue(venue['id'])

def search(company):
    """Search Foursquare's API for a match for a given company Series"""
    params = dict(DEFAULT_PARAMS)
    params.update({ 'query': company['trade_name'],
                    'll': '%s,%s' % (company['latitude'], company['longitude']),
                    'zip_code': company['zip_code'],
                    'intent': 'match' })
    url = 'https://api.foursquare.com/v2/venues/search'
    response = requests.get(url, params=params)
    if 200 >= response.status_code < 300:
        return parse_search_results(response)

def parse_search_results(response):
    """Return the first venue from the given search response"""
    json = response.json()
    venues = json['response']['venues']
    if venues:
        return venues[0]

def fetch_venue(venue_id):
    """Return specific data from Foursquare for the given venue_id"""
    url = 'https://api.foursquare.com/v2/venues/%s' % venue_id
    response = requests.get(url, params=DEFAULT_PARAMS)
    if 200 >= response.status_code < 300:
        return parse_venue_info(response)

def parse_venue_info(response):
    """Return only venue data from the given fetch_venue response"""
    json = response.json()
    venue = json['response']['venue']
    return venue

def write_fetched_companies(companies):
    """Save a CSV file """
    companies.to_csv(FOURSQUARE_DATASET_PATH,
                     compression='xz',
                     index=False)

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
            print('Was found  : %s' % fetched['name'])
            fetched['trade_name'] = company['trade_name']
            fetched['cnpj'] = company['cnpj']
            fetched['scraped_at'] = datetime.datetime.utcnow().isoformat()
            normalized = json_normalize(fetched)
            fetched_companies = pd.concat([fetched_companies, normalized])
        else:
            print('There were no matches')

        if (index % 100) == 0:
            print('###########################################')
            print("%s requests made. Stopping to save." % index)
            write_fetched_companies(fetched_companies)
            print('###########################################')
