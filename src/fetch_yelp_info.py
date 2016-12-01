import json
import requests
import re
import os.path
import datetime
import configparser
from unicodedata import normalize
import pandas as pd
import numpy as np
from pandas.io.json import json_normalize


"""
Get your API access token

1. Create an Yelp account.
2. Create an app (https://www.yelp.com/developers/v3/manage_app).
3. Run this command in your terminal to get yout access_token:
  curl -X POST -F 'client_id=YOUR_CLIENT_ID' -F 'client_secret=YOUT_CLIENT_SECRET' https://api.yelp.com/oauth2/token
4. Get your 'access_token' from the response and add to the config.ini file.
"""


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
    all_companies = all_companies[all_companies['trade_name'].notnull()]
    # Cleaning up companies CNPJs
    all_companies['clean_cnpj'] = \
        all_companies['cnpj'].map(lambda cnpj: cnpj.replace(
            '.', '').replace('/', '').replace('-', ''))
    # Filtering only companies that are in meal reimbursements
    return all_companies[all_companies['clean_cnpj'].isin(meal_cnpjs)]


def find_newest_file(name):
    date_regex = re.compile('\d{4}-\d{2}-\d{2}')

    matches = (date_regex.findall(f) for f in os.listdir(DATA_DIR))
    dates = sorted(set([l[0] for l in matches if l]), reverse=True)

    for date in dates:
        filename = '{}-{}.xz'.format(date, name)
        filepath = os.path.join(DATA_DIR, filename)

        if os.path.isfile(filepath):
            return filepath


def remaining_companies(fetched_companies, companies):
    return companies[~companies['cnpj'].isin(fetched_companies['cnpj'])]


def load_companies_dataset():
    if os.path.exists(YELP_DATASET_PATH):
        return pd.read_csv(YELP_DATASET_PATH)
    else:
        return pd.DataFrame(columns=['cnpj'])


def parse_fetch_info(response):
    if response.status_code == 200:
        json = response.json()
        results = json['businesses']
        if results:
            return results[0]
    else:
        print('Response ==>', response.status_code)


def write_fetched_companies(companies):
    companies.to_csv(YELP_DATASET_PATH,
                     compression='xz',
                     index=False)
# ----------------------------
# Request to yelp API getting by trade name and address
# https://www.yelp.com/developers/documentation/v3/business_search


def fetch_yelp_info(**params):
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {"Authorization": "Bearer {}".format(ACCESS_TOKEN)}
    response = requests.get(url, headers=headers, params=params)
    return parse_fetch_info(response)


def standardize_name(name):
    new_name = normalize('NFKD', name).encode(
        'ASCII', 'ignore').decode('utf-8')
    return set(new_name.lower().split(' '))


DATA_DIR = 'data'
REIMBURSEMENTS_DATASET_PATH = find_newest_file('reimbursements')
COMPANIES_DATASET_PATH = find_newest_file('companies')
YELP_DATASET_PATH = os.path.join('data', 'yelp-companies.xz')

settings = configparser.RawConfigParser()
settings.read('config.ini')
ACCESS_TOKEN = settings.get('Yelp', 'AccessToken')


if __name__ == '__main__':
    companies_w_meal_expense = companies()
    fetched_companies = load_companies_dataset()
    companies_to_fetch = remaining_companies(
        fetched_companies, companies_w_meal_expense).reset_index()

    for index, company in companies_to_fetch.iterrows():
        print('%s: Fetching %s - City: %s' %
              (index, company['trade_name'], company['city']))

        fetched_company = fetch_yelp_info(term=company['trade_name'],
                                          location='BR',
                                          latitude=company['latitude'],
                                          longitude=company['longitude'])

        is_good_result = False
        if fetched_company:
            expected_name = standardize_name(company['trade_name'])
            result_name = standardize_name(fetched_company['name'])
            is_good_result = len(
                expected_name - result_name) / len(expected_name) < .3

        if is_good_result:
            print('Successfuly matched %s' % fetched_company['name'])
        else:
            print('Not found')
            fetched_company = {}

        record = json_normalize(fetched_company)
        record['scraped_at'] = datetime.datetime.utcnow().isoformat()
        record['trade_name'] = company['trade_name']
        record['cnpj'] = company['cnpj']
        fetched_companies = pd.concat([fetched_companies, record])

        if (index % 100) == 0 and index > 0:
            print('###########################################')
            print("%s requests made. Stopping to save." % index)
            write_fetched_companies(fetched_companies)
            print('###########################################')

    write_fetched_companies(fetched_companies)
