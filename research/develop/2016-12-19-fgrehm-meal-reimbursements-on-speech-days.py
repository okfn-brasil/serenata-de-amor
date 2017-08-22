
# coding: utf-8

# # Meal reimbursements on speech days
# 
# We have a new dataset that can tell us if a congressperson was in Brasilia giving a speech in the congress on a given date and we want to analyze the meal reimbursements made on those dates to find some patterns and suspicious activity.
# 
# The reasoning and step by step on cleaning up the data can be found on [this gist](https://gist.github.com/fgrehm/bb0e1f6fef55082074d9a0258cf45391)

# In[1]:

import os.path
import pandas as pd
import numpy as np
import os.path
from serenata_toolbox.speeches import Speeches

companies = pd.read_csv('../data/2016-09-03-companies.xz', low_memory=False)
companies['cnpj'] = companies['cnpj'].str.replace(r'[\.\/\-]', '')

if not os.path.isfile('../data/2016-12-15-speeches.xz'):
    print("Cached speeches dataset not found, downloading...")
    client = Speeches()
    # The API only lets us query for 360 days at most
    speeches = client.fetch('02/01/2015', '28/12/2015')
    speeches = speeches.append(client.fetch('29/12/2015', '15/12/2016'))
    speeches.sort_values('session_date', inplace=True)
    client.write_file("../data/2016-12-15-speeches.xz", speeches)
else:
    print("Loading speeches data from cache")

speeches = pd.read_csv('../data/2016-12-15-speeches.xz', low_memory=False)
print("Total speeches:", speeches.shape[0])

# Clean up the data, see https://gist.github.com/fgrehm/bb0e1f6fef55082074d9a0258cf45391 for background
speeches = speeches[~speeches['speech_speaker_party'].isnull()]
speeches['speech_speaker_name'] = speeches['speech_speaker_name'].str.replace('\s+\(PRESIDENTE\)', '')
speeches['speech_speaker_party'] = speeches['speech_speaker_party'].str.upper()
speeches['speech_speaker_party'] = speeches['speech_speaker_party'].str.replace('PDSB', 'PSDB')
speeches['session_date'] = pd.to_datetime(speeches['session_date'], format="%Y-%m-%dT%H:%M:%S")
speeches['speech_started_at'] = pd.to_datetime(speeches['speech_started_at'], format="%Y-%m-%dT%H:%M:%S")
speeches = speeches[[
    'session_date',
    'speech_speaker_name', 
    'speech_speaker_party',
    'speech_speaker_state',
    'speech_started_at',
]]
print("Speeches by politicians in 2015-2016:", speeches.shape[0])

reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz', dtype={'cnpj_cpf': np.str}, low_memory=False)
print("Total reimbursements:", reimbursements.shape[0])

# Reduce dataset to 2015 and 2016 reimbursements
reimbursements = reimbursements[reimbursements['year'] >= 2015]
reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], format="%Y-%m-%dT%H:%M:%S")
print("Reimbursements in 2015-2016:", reimbursements.shape[0])

# extract list of congress people
congressperson_list = reimbursements[['applicant_id', 'congressperson_name', 'party', 'state', 'congressperson_id', 'congressperson_document']]
congressperson_list['party'] = congressperson_list['party'].str.upper()
congressperson_list = congressperson_list.drop_duplicates('congressperson_id', keep='first')
print("Congress person with reimbursements in that period:", congressperson_list.shape[0])

# match speeches with data from reimbursements so we can do a proper lookup
congressperson_in_brasilia = pd.merge(speeches, 
                                      congressperson_list, 
                                      left_on=['speech_speaker_name', 'speech_speaker_party', 'speech_speaker_state'],
                                      right_on=['congressperson_name', 'party', 'state'])

speech_with_match = ~congressperson_in_brasilia['congressperson_name'].isnull()
print("Speeches with matching congressperson:", congressperson_in_brasilia[speech_with_match].shape[0])

# Extract first and last speech on a day so that we have an idea of how long the person was there
period_in_brasilia = congressperson_in_brasilia.copy()
period_in_brasilia['first_speech_at'] = congressperson_in_brasilia['speech_started_at']
period_in_brasilia['last_speech_at'] = congressperson_in_brasilia['speech_started_at']
period_in_brasilia['total_speeches'] = 0
aggregations = {
    'last_speech_at': 'max',
    'first_speech_at': 'min',
    'total_speeches': 'count',
}
period_in_brasilia = period_in_brasilia.groupby(['applicant_id', 'session_date'], as_index=False).agg(aggregations)
print("Days with speeches:", period_in_brasilia.shape[0])

reimbursements_while_in_brasilia = pd.merge(
    reimbursements,
    period_in_brasilia,
    left_on=['applicant_id', 'issue_date'],
    right_on=['applicant_id', 'session_date']
)
print("Reimbursements made while in brasilia:", reimbursements_while_in_brasilia.shape[0])


# In[2]:

reimbursements_while_in_brasilia['subquota_description'].value_counts()


# In[3]:

meals_while_in_brasilia = reimbursements_while_in_brasilia[
    reimbursements_while_in_brasilia['subquota_description'] == 'Congressperson meal']

meals_while_in_brasilia = pd.merge(
    meals_while_in_brasilia, 
    companies[['cnpj', 'city', 'state', 'main_activity', 'name']], 
    left_on='cnpj_cpf', 
    right_on='cnpj',
    suffixes=('_congressperson', '_reimbursement')
)
print("Meals while in Brasilia:", meals_while_in_brasilia.shape[0])

meals_outside_brasilia_while_in_brasilia = meals_while_in_brasilia[                                             meals_while_in_brasilia['state_reimbursement'] != 'DF']
print("Meals outside DF while in Brasilia:", meals_outside_brasilia_while_in_brasilia.shape[0])


# I went through some of the list above and found out that most of the "weird" reimbursements were related to people that had given multiple speeches in a day and had lunch in a city away from Brasilia. Also, there are reimbursements related to buying food in flights so I excluded those from the list.

# In[4]:

not_gol = meals_outside_brasilia_while_in_brasilia['name'] != 'VRG LINHAS AEREAS S.A.'
meals_outside_brasilia_while_in_brasilia = meals_outside_brasilia_while_in_brasilia[not_gol]

def meal_with_speech_around_lunch(meal):
    if meal['total_speeches'] > 1:
        return meal['first_speech_at'].hour <= 12 and meal['last_speech_at'].hour >= 12
    else:
        return False

suspects = meals_outside_brasilia_while_in_brasilia[
    meals_outside_brasilia_while_in_brasilia.apply(meal_with_speech_around_lunch, axis=1)
]
print("Suspicious meals:", suspects.shape[0])


# In[5]:

from IPython.display import HTML

report = suspects[[
   'issue_date', 'congressperson_name', 'document_id', 'total_speeches', 'first_speech_at', 'last_speech_at',
   'total_net_value', 'state_congressperson', 'state_reimbursement', 'city'
]].rename(index=str, columns={"city": "city_reimbursement"})

report['document_id'] = report['document_id'].apply(lambda x: '<a target="_blank" href="http://jarbas.datasciencebr.com/#/document_id/{0}">{0}</a>'.format(x))
report.sort_values(['congressperson_name', 'first_speech_at'], inplace=True)

pd.set_option('display.max_colwidth', 1000)
HTML(report.to_html(escape=False))


# I got those into a spreadsheet any manually checked if the times of the receipts are within the period that the deputy was giving a speech and found 10 that look suspicious.
# 
# ## Future work / random thoughts
# 
# - We can't automate this analysis yet because we don't have the timestamp of when the purchase was made, once we have that around things will be much easier.
# - We can feed in this information about the person being in Brasilia into the logic we already have for travelled distance between meals (this would be another node in the graph of travels).
# - Matching of speakers and congresspeople can be improved.
