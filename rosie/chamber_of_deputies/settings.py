from rosie.chamber_of_deputies.classifiers import ElectionExpensesClassifier
from rosie.chamber_of_deputies.classifiers import IrregularCompaniesClassifier
from rosie.chamber_of_deputies.classifiers import MealPriceOutlierClassifier
from rosie.chamber_of_deputies.classifiers import MonthlySubquotaLimitClassifier
from rosie.chamber_of_deputies.classifiers import TraveledSpeedsClassifier
from rosie.core.classifiers import InvalidCnpjCpfClassifier

CLASSIFIERS = {
    'meal_price_outlier': MealPriceOutlierClassifier,
    'over_monthly_subquota_limit': MonthlySubquotaLimitClassifier,
    'suspicious_traveled_speed_day': TraveledSpeedsClassifier,
    'invalid_cnpj_cpf': InvalidCnpjCpfClassifier,
    'election_expenses': ElectionExpensesClassifier,
    'irregular_companies_classifier': IrregularCompaniesClassifier
}

UNIQUE_IDS = ['applicant_id', 'year', 'document_id']
