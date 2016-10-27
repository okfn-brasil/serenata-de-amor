import configparser
from df2gspread import gspread2df as g2d
import numpy as np
import pandas as pd
from random import sample

"""
This script requires the existence of 2 files:
    * `data/volunteers.csv`. Private, containing emails of investigators.
        e.g.

        "Email (é por ele que iremos manter contato)"
        john@example.com
        michael@example.com
        hannah@example.com
        barbara@example.com
        susan@example.com

    * Spreadsheet hosted at Google Drive. Private, containing cases.
        e.g.

        document_id,case,investigators,investigators_working
        1000,1,"john@example.com,michael@example.com,hannah@example.com","john@example.com"
        1001,1,"john@example.com,michael@example.com,hannah@example.com","john@example.com"
        1002,1,"john@example.com,michael@example.com,hannah@example.com","john@example.com"
        1050,1,"barbara@example.com,susan@example.com",
"""

INVESTIGATOR_EMAIL_COLUMN = 'Email (é por ele que iremos manter contato)'

def distribute_cases(cases, investigators):
    batch = dict()
    for _, row in cases.drop_duplicates('case').iterrows():
        n = row['missing_investigators']
        already_in_this_case = set(np.hstack(row['investigators'].split(',')))
        available_investigators = investigators - \
            already_in_this_case - \
            set(batch.keys())
        random_investigators = sample(available_investigators, n)
        for email in random_investigators:
            batch[email] = row['case']
    return batch



settings = configparser.RawConfigParser()
settings.read('config.ini')
cases_document = settings.get('Google', 'CasesDocument')

cases = g2d.download(gfile=cases_document, col_names=True)
investigator_columns = ['investigators', 'investigators_working']
cases['case'] = cases['case'].astype(np.int)
cases[investigator_columns] = cases[investigator_columns].astype(np.str)
cases['missing_investigators'] = 3 - cases['investigators'].str.count('@')
investigators_working = cases.loc[cases['investigators_working'].notnull(),
                                  'investigators_working'].str.split(',').values
investigators_working = set(np.hstack(investigators_working)) - {''}

investigators = pd.read_csv('data/volunteers.csv')
all_investigators = set(investigators[INVESTIGATOR_EMAIL_COLUMN]) - \
    investigators_working

print(distribute_cases(cases, all_investigators))
