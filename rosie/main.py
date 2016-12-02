import os
import numpy as np
import pandas as pd
from serenata_toolbox.ceap_dataset import CEAPDataset
from serenata_toolbox.datasets import fetch
from monthly_subquota_limit_classifier import MonthlySubquotaLimitClassifier
from traveled_speeds_classifier import TraveledSpeedsClassifier

DATA_PATH = '/tmp/serenata-data'
DATASET_KEYS = ['applicant_id', 'year', 'document_id']
COMPANIES_DATASET = '2016-09-03-companies.xz'
CLASSIFIERS = {
    MonthlySubquotaLimitClassifier: 'over_monthly_subquota_limit',
    TraveledSpeedsClassifier: 'day_traveled_speed',
}


def update_datasets():
    os.makedirs(DATA_PATH, exist_ok=True)
    ceap = CEAPDataset(DATA_PATH)
    ceap.fetch()
    ceap.convert_to_csv()
    ceap.translate()
    ceap.clean()
    fetch(COMPANIES_DATASET, DATA_PATH)


def get_reimbursements():
    dataset = \
        pd.read_csv(os.path.join(DATA_PATH, 'reimbursements.xz'),
                    dtype={'applicant_id': np.str,
                           'cnpj_cpf': np.str,
                           'congressperson_id': np.str,
                           'subquota_number': np.str},
                    low_memory=False)
    dataset['issue_date'] = pd.to_datetime(dataset['issue_date'],
                                           errors='coerce')
    return dataset


def get_companies():
    is_in_brazil = '(-73.992222 < longitude < -34.7916667) & (-33.742222 < latitude < 5.2722222)'
    dataset = pd.read_csv(os.path.join(DATA_PATH, COMPANIES_DATASET),
                          dtype={'cnpj_cpf': np.str},
                          low_memory=False)
    dataset = dataset.query(is_in_brazil)
    dataset['cnpj'] = dataset['cnpj'].str.replace(r'\D', '')
    return dataset


def run_classifiers(data):
    irregularities = data[DATASET_KEYS].copy()

    for classifier, irregularity in CLASSIFIERS.items():
        model = classifier()
        model.fit_transform(data)
        irregularities[irregularity] = model.predict(data)

    irregularities.to_csv(os.path.join(DATA_PATH, 'irregularities.xz'),
                          compression='xz',
                          encoding='utf-8',
                          index=False)


if __name__ == '__main__':
    update_datasets()

    reimbursements = get_reimbursements()
    companies = get_companies()
    dataset = pd.merge(reimbursements, companies,
                       left_on='cnpj_cpf',
                       right_on='cnpj')
    run_classifiers(dataset)
