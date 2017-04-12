import os.path

import numpy as np
from sklearn.externals import joblib

from ceap.classifiers.dataset import Dataset
from ceap.classifiers.election_expenses_classifier import ElectionExpensesClassifier
from ceap.classifiers.invalid_cnpj_cpf_classifier import InvalidCnpjCpfClassifier
from ceap.classifiers.meal_price_outlier_classifier import MealPriceOutlierClassifier
from ceap.classifiers.monthly_subquota_limit_classifier import MonthlySubquotaLimitClassifier
from ceap.classifiers.traveled_speeds_classifier import TraveledSpeedsClassifier
from ceap.classifiers.irregular_companies_classifier import IrregularCompaniesClassifier


class Ceap:
    CLASSIFIERS = {
        MealPriceOutlierClassifier: 'meal_price_outlier',
        MonthlySubquotaLimitClassifier: 'over_monthly_subquota_limit',
        TraveledSpeedsClassifier: 'suspicious_traveled_speed_day',
        InvalidCnpjCpfClassifier: 'invalid_cnpj_cpf',
        ElectionExpensesClassifier: 'election_expenses',
        IrregularCompaniesClassifier: 'irregular_companies_classifier'
    }
    DATASET_KEYS = ['applicant_id', 'year', 'document_id']

    def __init__(self, dataset, data_path):
        self.dataset = dataset
        self.data_path = data_path
        self.irregularities = self.dataset[self.DATASET_KEYS].copy()

    def run_classifiers(self):
        for classifier, irregularity in self.CLASSIFIERS.items():
            model = self.load_trained_model(classifier)
            self.predict(model, irregularity)

        self.irregularities.to_csv(os.path.join(self.data_path, 'irregularities.xz'),
                                   compression='xz',
                                   encoding='utf-8',
                                   index=False)

    def load_trained_model(self, classifier):
        filename = '{}.pkl'.format(classifier.__name__.lower())
        path = os.path.join(self.data_path, filename)
        # palliative since this model is outputting
        # a model too large to be loaded with joblib
        if filename == 'monthlysubquotalimitclassifier.pkl':
            model = classifier()
            model.fit(self.dataset)
        else:
            if os.path.isfile(path):
                model = joblib.load(path)
            else:
                model = classifier()
                model.fit(self.dataset)
                joblib.dump(model, path)
        return model

    def predict(self, model, irregularity):
        model.transform(self.dataset)
        y = model.predict(self.dataset)
        self.irregularities[irregularity] = y
        if y.dtype == np.int:
            self.irregularities.loc[y == 1, irregularity] = False
            self.irregularities.loc[y == -1, irregularity] = True


def main(target_directory='/tmp/serenata-data'):
    dataset = Dataset(target_directory).get()
    Ceap(dataset, target_directory).run_classifiers()
