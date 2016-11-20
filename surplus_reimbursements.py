from datetime import datetime
import pandas as pd
import numpy as np

KEYS = ['applicant_id', 'month', 'year']

def create_cumsum_cols(subset):
    subset['cumsum_net_value'] = subset['net_value_int'].cumsum()
    return subset

def find_surplus_reimbursements(data, monthly_limit):
    grouped = data.groupby(KEYS).apply(create_cumsum_cols)
    return grouped[grouped['cumsum_net_value'] > monthly_limit]



dataset = pd.read_csv('/tmp/serenata-data/2016-11-20-reimbursements.xz',
                      parse_dates=['issue_date'],
                      dtype={'applicant_id': np.str,
                            'batch_number': np.str,
                            'cnpj_cpf': np.str,
                            'congressperson_document': np.str,
                            'congressperson_id': np.str,
                            'document_id': np.str,
                            'document_number': np.str,
                            'document_type': np.str,
                            'leg_of_the_trip': np.str,
                            'passenger': np.str,
                            'reimbursement_number': np.str,
                            'subquota_group_description': np.str,
                            'subquota_group_id': np.str,
                            'subquota_number': np.str,
                            'term_id': np.str,
                      },
                      low_memory=False)

dataset['net_value_int'] = (dataset['total_net_value'] * 100).apply(int)

dataset['coerced_issue_date'] = \
    pd.to_datetime(dataset['issue_date'], errors='coerce')
dataset.sort_values('coerced_issue_date', inplace=True)

reimbursement_month = dataset[['year', 'month']].copy()
reimbursement_month['day'] = 1
dataset['reimbursement_month'] = pd.to_datetime(reimbursement_month)

subquota_limits = [
    {
        'subquota': 'Automotive vehicle renting or watercraft charter',
        'data': dataset.query('(subquota_number == "120") & (reimbursement_month >= datetime(2015, 4, 1))'),
        'monthly_limit': 1090000,
    },
    {
        'subquota': 'Taxi, toll and parking',
        'data': dataset.query('(subquota_number == "122") & (reimbursement_month >= datetime(2015, 4, 1))'),
        'monthly_limit': 270000,
    },
    {
        'subquota': 'Fuels and lubricants',
        'data': dataset.query('(subquota_number == "3") & (reimbursement_month >= datetime(2015, 10, 1))'),
        'monthly_limit': 600000,
    },
    {
        'subquota': 'Security service provided by specialized company',
        'data': dataset.query('(subquota_number == "8") & (reimbursement_month >= datetime(2015, 4, 1))'),
        'monthly_limit': 870000,
    },
    {
        'subquota': 'Participation in course, talk or similar event',
        'data': dataset.query('(subquota_number == "137") & (reimbursement_month >= datetime(2015, 11, 1))'),
        'monthly_limit': 769716,
    },
]

dataset['is_over_monthly_subquota_limit'] = False

for metadata in subquota_limits:
    data, monthly_limit = metadata['data'], metadata['monthly_limit']
    surplus_reimbursements = find_surplus_reimbursements(data, monthly_limit)
    dataset.loc[surplus_reimbursements.index, 'is_over_monthly_subquota_limit'] = True

dataset[dataset['is_over_monthly_subquota_limit']].shape
