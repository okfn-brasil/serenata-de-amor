import os.path
import requests
import numpy as np
import pandas as pd
import re
import json
import datetime

# Setting dataset paths
REIMBURSEMENTS_DATASET_PATH = os.path.join('data', '2016-11-22-reimbursements.xz')
COMPANIES_DATASET_PATH = os.path.join('data', '2016-09-03-companies.xz')
FOURSQUARE_DATASET_PATH = os.path.join('data', 'foursquare-companies.json')

# These are the keys to access Foursquare's API. You can create your own through the link bellow
# https://pt.foursquare.com/developers/register
CLIENT_ID = ''
CLIENT_SECRET = ''
# This is in YYYYMMDD format.
VERSION = '20161021'

# Required params to make a request to Foursquare's API
DEFAULT_PARAMS = {'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'v': VERSION}


def companies():
    # Loading reimbursements
    docs = pd.read_csv(REIMBURSEMENTS_DATASET_PATH,
                       low_memory=False,
                       dtype={'cnpj_cpf': np.str})
    # Filtering only congressperson meals
    meal_docs = docs[docs.subquota_description == 'Congressperson meal']
    # Storing only unique CNPJs
    meal_cnpjs = meal_docs['cnpj_cpf'].unique()

    # Loading companies
    all_companies = pd.read_csv(COMPANIES_DATASET_PATH,
                                low_memory=False,
                                dtype={'trade_name': np.str})
    # Cleaning up companies CNPJs
    all_companies['clean_cnpj'] = all_companies['cnpj'].map(cleanup_cnpj)
    # Filtering only companies that are in meal reimbursements
    return all_companies[all_companies['clean_cnpj'].isin(meal_cnpjs)]

def cleanup_cnpj(cnpj):
    regex = r'\d'
    digits = re.findall(regex, '%s' % cnpj)
    return ''.join(digits)

def remaining_companies(companies):
    df = load_foursquare_companies_dataset()
    return companies[~companies['cnpj'].isin(df['cnpj'])]

def load_foursquare_companies_dataset():
    if os.path.exists(FOURSQUARE_DATASET_PATH):
        return pd.read_json(FOURSQUARE_DATASET_PATH)
    else:
        return pd.DataFrame(columns=['cnpj'])

def get_venue(company):
    venue = search(company)
    if venue:
        return fetch_venue_by_id(venue['id'])

def search(company, timeout=5):
    params = dict(DEFAULT_PARAMS)
    params.update({
        'query': company['trade_name'],
        'll': '%s,%s' % (company['latitude'], company['longitude']),
        'zip_code': company['zip_code'],
        'intent': 'match'
    })
    url = 'https://api.foursquare.com/v2/venues/search'
    response = requests.get(url, params=params)

    return parse_search_results(response)

def parse_search_results(response):
    json = response.json()
    if json['meta']['code'] == 200:
        venues = json['response']['venues']
        if venues:
            return venues[0]

def fetch_venue_by_id(venue_id):
    url = 'https://api.foursquare.com/v2/venues/%s' % venue_id
    response = requests.get(url, params=DEFAULT_PARAMS)

    return parse_venue_info(response)

def parse_venue_info(response):
    json = response.json()
    if json['meta']['code'] == 200:
        return json['response']['venue']

fetched_companies = []

for _, company in remaining_companies(companies()[500]).iterrows():
    print('Fetching %s - CNPJ: %s' % (company['trade_name'], company['cnpj']))
    fetched_company = get_venue(company)
    if fetched_company:
        print('Successifuly matched %s' % fetched_company['name'])
        fetched_company['scraped_at'] = datetime.datetime.utcnow().isoformat()
        fetched_company['cnpj'] = company['cnpj']
        fetched_companies.append(fetched_company)
    else:
        print('Not found')

if fetched_companies:
    print('Saving it all!')
    with open(FOURSQUARE_DATASET_PATH, 'w') as outfile:
        json.dump(fetched_companies, outfile)
else:
    print('Nothing to save.')
