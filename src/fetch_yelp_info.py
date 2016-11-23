import json
import requests
import re
import os.path
import datetime
import configparser
import pandas as pd
import numpy as np

REIMBURSEMENTS_DATASET_PATH = os.path.join('data', '2016-11-19-reimbursements.xz')
COMPANIES_DATASET_PATH = os.path.join('data', '2016-09-03-companies.xz')
YELP_DATASET_PATH = os.path.join('data', 'yelp-companies.xz')

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
  all_companies['clean_cnpj'] = all_companies['cnpj'].map(cleanup_cnpj)
  # Filtering only companies that are in meal reimbursements
  return all_companies[all_companies['clean_cnpj'].isin(meal_cnpjs)]

def cleanup_cnpj(cnpj):
  regex = r'\d'
  digits = re.findall(regex, '%s' % cnpj)
  return ''.join(digits)

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

# ----------------------------
# Request to yelp API getting by term and zip code
# https://www.yelp.com/developers/documentation/v3/business_search
def fetch_yelp_info(**params):
  url = 'https://api.yelp.com/v3/businesses/search'
  headers = {"Authorization":"Bearer {}".format(access_token)}
  response = requests.get(url, headers=headers, params=params);
  return parse_fetch_info(response)

settings = configparser.RawConfigParser()
settings.read('config.ini')
access_token = settings.get('Yelp', 'AccessToken')

companies_w_meal_expense = companies()

fetched_companies = load_companies_dataset()
companies_to_fetch = remaining_companies(fetched_companies, companies())[:50]

import pdb; pdb.set_trace()
for _, company in companies_to_fetch.iterrows():
    print('Fetching %s - City: %s' % (company['trade_name'], company['city']))

    address_to_search = "{}, {}, {}".format(company['neighborhood'], company['city'], company['state'])
    fetched_company = fetch_yelp_info(term=company['trade_name'], location=address_to_search)

    if fetched_company:
        print('Successfuly matched %s' % fetched_company['name'])
        fetched_company['scraped_at'] = datetime.datetime.utcnow().isoformat()
        fetched_company['cnpj'] = company['cnpj']
        fetched_companies = fetched_companies.append(pd.Series(fetched_company),
                                                     ignore_index=True)
    else:
        print('Not found')

fetched_companies.to_csv(YELP_DATASET_PATH, compression='xz', index=False)
