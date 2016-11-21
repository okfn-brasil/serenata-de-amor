import os
import numpy as np
import pandas as pd
from serenata_toolbox.ceap_dataset import CEAPDataset
from monthly_subquota_limit_classifier import MonthlySubquotaLimitClassifier

DATA_PATH = '/tmp/serenata-data'
DATASET_KEYS = ['applicant_id', 'year', 'document_id']

def update_datasets(self):
    os.makedirs(self.DATA_PATH, exist_ok=True)
    ceap = CEAPDataset(self.DATA_PATH)
    ceap.fetch()
    ceap.convert_to_csv()
    ceap.translate()
    ceap.clean()


def run_classifiers(data):
    irregularities = data[DATASET_KEYS].copy()
    model = MonthlySubquotaLimitClassifier()
    model.fit_transform(data)
    irregularities['over_monthly_subquota_limit'] = model.predict(data)
    irregularities.to_csv(os.path.join(DATA_PATH, 'irregularities.xz'),
                          compression='xz',
                          encoding='utf-8',
                          index=False)



if __name__ == '__main__':
    update_datasets()

    dataset = pd.read_csv(os.path.join(DATA_PATH, 'reimbursements.xz'),
                          dtype={'applicant_id': np.str,
                                 'subquota_number': np.str},
                          low_memory=False)
    run_classifiers(dataset)
