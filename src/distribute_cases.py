import configparser
from df2gspread import gspread2df as g2d
import numpy as np
from os.path import expanduser, isfile
import pandas as pd
from random import sample

"""
This script requires the existence of 3 files:
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
        1050,2,"barbara@example.com,susan@example.com",

    * `~/.gdrive_private`. Needed to access your Google Drive documents.
        Check the following link for further instructions.
        https://github.com/maybelinot/df2gspread#access-credentials
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

def read_cases_document():
    file_path = expanduser('~') + '/.gdrive_private'
    if not isfile(file_path):
        raise FileNotFoundError('{} must exist'.format(file_path))
    settings = configparser.RawConfigParser()
    settings.read('config.ini')
    cases_document = settings.get('Google', 'CasesDocument')
    return g2d.download(gfile=cases_document, col_names=True)




cases = read_cases_document()
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
