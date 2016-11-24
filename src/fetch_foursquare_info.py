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

def load_cnpjs(subquota_description):
    u_cols = ['cnpj_cpf', 'subquota_description']
    docs = pd.read_csv(REIMBURSEMENTS_DATASET_PATH,
                        low_memory=False,
                        usecols=u_cols,
                        dtype={'cnpj_cpf': np.str})
    meals = docs[docs.subquota_description == subquota_description]
    return meals['cnpj_cpf'].unique()

def load_companies():
    u_cols = ['cnpj', 'trade_name', 'zip_code', 'latitude', 'longitude']
    all_companies = pd.read_csv(COMPANIES_DATASET_PATH,
                                low_memory=False,
                                usecols=u_cols,
                                dtype={'trade_name': np.str})
    all_companies['clean_cnpj'] = all_companies['cnpj'].map(cleanup_cnpj)
    relevant_cnpjs = load_cnpjs('Congressperson meal')
    return all_companies[all_companies['clean_cnpj'].isin(relevant_cnpjs)]

def cleanup_cnpj(cnpj):
    return re.sub("\D", "", cnpj)

def remaining_companies(companies):
    fetched_companies = load_foursquare_companies_dataset()
    return companies[~companies['cnpj'].isin(fetched_companies['cnpj'])]

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
        venue = json['response']['venue']
        current_time = datetime.datetime.utcnow().isoformat()
        venue['scraped_at'] = current_time
        return venue

def write_fetched_companies(companies):
    with open(FOURSQUARE_DATASET_PATH, 'w') as outfile:
        json.dump(fetched_companies, outfile)

if __name__ == '__main__':
    all_companies = load_companies()
    remaining_companies = remaining_companies(all_companies)
    fetched_companies = []

    if not (CLIENT_ID and CLIENT_SECRET):
        raise 'Missing API credentials'

    for index, company in remaining_companies.iterrows():
        print('Looking for: %s' % company['trade_name'])
        fetched_company = get_venue(company)
        if fetched_company:
            print('Was found  : %s' % fetched_company['name'])
            fetched_company['cnpj'] = company['cnpj']
            fetched_companies.append(fetched_company)
        else:
            print('There were no matches')

        print('')

        if (index % 100) == 0:
            print('###########################################')
            print("%s requests made. Stopping to save." % index)
            if fetched_companies:
                write_fetched_companies(fetched_companies)
                fetched_companies = []
            else:
                print('Nothing to save.')
            print('###########################################')
            print('')
