import json
import requests
import re
import os.path
import datetime
import configparser
import pandas as pd
import numpy as np
from pandas.io.json import json_normalize



REIMBURSEMENTS_DATASET_PATH = os.path.join('data', '2016-11-19-reimbursements.xz')
COMPANIES_DATASET_PATH = os.path.join('data', '2016-09-03-companies.xz')
YELP_DATASET_PATH = os.path.join('data', 'yelp-companies.xz')

"""
Get your access token

1. Create an Yelp account.
2. Create an app (https://www.yelp.com/developers/v3/manage_app).
3. Run this command in your terminal to get yout access_token:
  curl -X POST -F 'client_id=YOUR_CLIENT_ID' -F 'client_secret=YOUT_CLIENT_SECRET' https://api.yelp.com/oauth2/token
4. Get your 'access_token' from the response and add to the config.ini file.
"""

settings = configparser.RawConfigParser()
settings.read('config.ini')
ACCESS_TOKEN = settings.get('Yelp', 'AccessToken')



# Functions
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
# Request to yelp API getting by trade name and address
# https://www.yelp.com/developers/documentation/v3/business_search
def fetch_yelp_info(**params):
  url = 'https://api.yelp.com/v3/businesses/search'
  headers = {"Authorization":"Bearer {}".format(ACCESS_TOKEN)}
  response = requests.get(url, headers=headers, params=params);
  return parse_fetch_info(response)



companies_w_meal_expense = companies()

fetched_companies = load_companies_dataset()
companies_to_fetch = remaining_companies(fetched_companies, companies())

for _, company in companies_to_fetch.iterrows():
    print('Fetching %s - City: %s' % (company['trade_name'], company['city']))

    address_to_search = "{}, {}, {}".format(company['neighborhood'], company['city'], company['state'])
    fetched_company = fetch_yelp_info(term=company['trade_name'], location=address_to_search)

    if fetched_company:
        print('Successfuly matched %s' % fetched_company['name'])
        normalized = json_normalize(fetched_company)
        normalized['scraped_at'] = datetime.datetime.utcnow().isoformat()
        normalized['trade_name'] = company['trade_name']
        normalized['cnpj'] = company['cnpj']
        fetched_companies = pd.concat([fetched_companies, normalized])
    else:
        print('Not found')

fetched_companies.to_csv(YELP_DATASET_PATH, compression='xz', index=False)
