import numpy as np
import pandas as pd
from sklearn.base import TransformerMixin


class MonthlySubquotaLimitClassifier(TransformerMixin):
    """
    Monthly Subquota Limit classifier.

    Dataset
    -------
    issue_date : datetime column
        Date when the expense was made.

    month : int column
        The quota month matching the expense request.

    net_value : float column
        The value of the expense.

    subquota_number : category column
        A number to classify a category of expenses.

    year : int column
        The quota year matching the expense request.
    """

    KEYS = ['applicant_id', 'month', 'year']
    COLS = ['applicant_id',
            'issue_date',
            'month',
            'net_value',
            'subquota_number',
            'year']

    def fit(self, X):
        self.X = X
        self._X = self.X[self.COLS].copy()
        self.__create_columns()
        return self

    def transform(self, X=None):
        self.limits = [
            {
                # Automotive vehicle renting or charter (From 12/2013 to 03/2015)
                'data': self._X.query('(subquota_number == "120") & '
                                      '(reimbursement_month >= datetime(2013, 12, 1)) & '
                                      '(reimbursement_month <= datetime(2015, 3, 1))'),
                'monthly_limit': 1000000,
            },
            {
                # Automotive vehicle renting or charter (From 04/2015 to 04/2017)
                'data': self._X.query('(subquota_number == "120") & '
                                      '(reimbursement_month >= datetime(2015, 4, 1)) & '
                                      '(reimbursement_month <= datetime(2017, 4, 1))'),
                'monthly_limit': 1090000,
            },
            {
                # Automotive vehicle renting or charter (From 05/2017)
                'data': self._X.query('(subquota_number == "120") & '
                                      '(reimbursement_month >= datetime(2017, 5, 1))'),
                'monthly_limit': 1271300,
            },
            {
                # Taxi, toll and parking (From 12/2013 to 03/2015)
                'data': self._X.query('(subquota_number == "122") & '
                                      '(reimbursement_month >= datetime(2013, 12, 1)) & '
                                      '(reimbursement_month <= datetime(2015, 3, 1))'),
                'monthly_limit': 250000,
            },
            {
                # Taxi, toll and parking (From 04/2015)
                'data': self._X.query('(subquota_number == "122") & '
                                      '(reimbursement_month >= datetime(2015, 4, 1))'),
                'monthly_limit': 270000,
            },
            {
                # Fuels and lubricants (From 07/2009 to 03/2015)
                'data': self._X.query('(subquota_number == "3") & '
                                      '(reimbursement_month >= datetime(2009, 7, 1)) & '
                                      '(reimbursement_month <= datetime(2015, 3, 1))'),
                'monthly_limit': 450000,
            },
            {
                # Fuels and lubricants (From 04/2015 to 08/2015)
                'data': self._X.query('(subquota_number == "3") & '
                                      '(reimbursement_month >= datetime(2015, 4, 1)) & '
                                      '(reimbursement_month <= datetime(2015, 8, 1))'),
                'monthly_limit': 490000,
            },
            {
                # Fuels and lubricants (From 9/2015)
                'data': self._X.query('(subquota_number == "3") & '
                                      '(reimbursement_month >= datetime(2015, 9, 1))'),
                'monthly_limit': 600000,
            },
            {
                # Security service provided by specialized company (From 07/2009 to 4/2014)
                'data': self._X.query('(subquota_number == "8") & '
                                      '(reimbursement_month >= datetime(2009, 7, 1)) & '
                                      '(reimbursement_month <= datetime(2014, 4, 1))'),
                'monthly_limit': 450000,
            },
            {
                # Security service provided by specialized company (From 05/2014 to 3/2015)
                'data': self._X.query('(subquota_number == "8") & '
                                      '(reimbursement_month >= datetime(2014, 5, 1)) & '
                                      '(reimbursement_month <= datetime(2015, 3, 1))'),
                'monthly_limit': 800000,
            },
            {
                # Security service provided by specialized company (From 04/2015)
                'data': self._X.query('(subquota_number == "8") & '
                                      '(reimbursement_month >= datetime(2015, 4, 1))'),
                'monthly_limit': 870000,
            },
            {
                # Participation in course, talk or similar event (From 10/2015)
                'data': self._X.query('(subquota_number == "137") & '
                                      '(reimbursement_month >= datetime(2015, 10, 1))'),
                'monthly_limit': 769716,
            },
        ]
        return self

    def predict(self, X=None):
        self._X['is_over_monthly_subquota_limit'] = False
        for metadata in self.limits:
            data, monthly_limit = metadata['data'], metadata['monthly_limit']
            if len(data):
                surplus_reimbursements = self.__find_surplus_reimbursements(data, monthly_limit)
                self._X.loc[surplus_reimbursements.index,
                            'is_over_monthly_subquota_limit'] = True
        results = self._X.loc[self.X.index, 'is_over_monthly_subquota_limit']
        return np.r_[results]

    def predict_proba(self, X=None):
        return 1.

    def __create_columns(self):
        self._X['net_value_int'] = (self._X['net_value'] * 100).apply(int)

        self._X['coerced_issue_date'] = \
            pd.to_datetime(self._X['issue_date'], errors='coerce')
        self._X.sort_values('coerced_issue_date', kind='mergesort', inplace=True)

        reimbursement_month = self._X[['year', 'month']].copy()
        reimbursement_month['day'] = 1
        self._X['reimbursement_month'] = pd.to_datetime(reimbursement_month)

    def __find_surplus_reimbursements(self, data, monthly_limit):
        grouped = data.groupby(self.KEYS).apply(self.__create_cumsum_cols)
        return grouped[grouped['cumsum_net_value'] > monthly_limit]

    def __create_cumsum_cols(self, subset):
        subset['cumsum_net_value'] = subset['net_value_int'].cumsum()
        return subset
