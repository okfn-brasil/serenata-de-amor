
# coding: utf-8

# # Analysis on meals based on presence information
# 
# We've already submited many inquiries about meals made outside DF while deputies were supposed to be in DF and also meals in DF while deputies were supposed to be somewhere else (like in another country on an official mission). This notebook outlines all types of analysis we can do around that with datasets we currently have around and it also makes use of more recent versions of datasets we've collected over the past couple months.

# In[1]:

import re
import time
from datetime import timedelta

import pandas as pd
import numpy as np

from serenata_toolbox.datasets import fetch


# In[2]:

from IPython.display import HTML

def report(df, cols):
    df = df.copy()
    df['receipt'] = df.apply(link_to_receipt, axis=1)
    df['document_id'] = df.apply(link_to_jarbas, axis=1)
    return HTML(df[cols].to_html(escape=False))

def link_to_jarbas(r):
    return '<a target="_blank" href="http://jarbas.serenatadeamor.org/#/document_id/{0}">{0}</a>'.format(r.document_id)

DOCUMENT_URL = (
    'http://www.camara.gov.br/'
    'cota-parlamentar/documentos/publ/{}/{}/{}.pdf'
)
def link_to_receipt(r):
    url = DOCUMENT_URL.format(r.applicant_id, r.year, r.document_id)
    return '<a target="_blank" href="{0}">RECEIPT</a>'.format(url)

pd.set_option('display.max_colwidth', 1500)


# ## Data preparation

# In[6]:

# fetch("2017-02-15-receipts-texts.xz", "../data")
# fetch("2017-03-15-reimbursements.xz", "../data")
fetch("2017-05-21-companies-no-geolocation.xz", "../data")

# TODO: Need to make sure the datasets have been uploaded to the S3 bucket
# fetch("2017-04-19-official-missions.xz", "../data")
# fetch("2017-05-29-session-start-times.xz", "../data")
# fetch("2017-05-29-presences.xz", "../data")
# fetch("2017-05-29-deputies.xz", "../data")
# fetch("2017-05-29-speeches.xz", "../data")


# In[7]:

reimbursements = pd.read_csv('../data/2017-03-15-reimbursements.xz', dtype={'cnpj_cpf': np.str}, low_memory=False)
print("Total reimbursements:", len(reimbursements))

# Reduce dataset to current term
reimbursements = reimbursements.query('year >= 2015')
reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], format="%Y-%m-%dT%H:%M:%S").dt.date
print("Reimbursements in this term:", len(reimbursements))

# Reduce dataset to meals
meals = reimbursements.query('subquota_description == "Congressperson meal"')
print("Meals in this term:", len(meals))


# In[8]:

companies = pd.read_csv('../data/2017-05-21-companies-no-geolocation.xz', low_memory=False)
companies['cnpj'] = companies['cnpj'].str.replace(r'[\.\/\-]', '')

# Reduce dataset to meals with matching company and state info
meals = pd.merge(
    meals, 
    companies[['cnpj', 'city', 'state', 'main_activity', 'name']], 
    left_on='cnpj_cpf', 
    right_on='cnpj',
    suffixes=('_congressperson', '_company')
)
print("Meals with matching companies:", len(meals))

meals = meals[~meals.state_company.isnull()]
print("Meals with known company state:", len(meals))
meals = meals.rename(index=str, columns={
    "state_congressperson": "congressperson_state",
    "name": "company_name", 
    "city": "company_city", 
    "state_company": "company_state"
})


# In[9]:

texts = pd.read_csv('../data/2017-02-15-receipts-texts.xz', dtype={'text': np.str}, low_memory=False)
texts['text'] = texts.text.str.upper()

meals_with_ts = texts.merge(meals[['document_id']], on='document_id')
print("Meals with OCR:", len(meals_with_ts))


# In[10]:

def extract_timestamps(text):
    return re.findall('[0-9][0-9]:[0-9][0-9]:[0-9][0-9]', str(text))
meals_with_ts['timestamps'] = meals_with_ts.text.apply(extract_timestamps)

def parse_timestamps(ts):
    try:
        return time.strptime(ts, "%H:%M:%S")
    except:
        return None
meals_with_ts['timestamps'] = meals_with_ts.timestamps.apply(lambda ts: list(map(parse_timestamps, ts)))
meals_with_ts = meals_with_ts[meals_with_ts.apply(lambda r: len(r.timestamps) > 0, axis=1)]

meals = pd.merge(
    left=meals,
    right=meals_with_ts[['document_id', 'timestamps']],
    how='left',
    on='document_id'
)
print("Meals with timestamps:", len(meals[~meals.timestamps.isnull()]))


# In[11]:

meals = meals[[
    'document_id',
    'applicant_id',
    'congressperson_document',
    'congressperson_id',
    'congressperson_name',
    'congressperson_state',
    'party',
    'year',
    'issue_date',
    'total_net_value',
    'company_name',
    'company_state',
    'timestamps'
]]


# ## Meals outside DF while the congressperson was present in a session
# 
# There are at least two ways we can identify that:
# * Making an approximation of the total time the congressperson was in Brasilia (like more than X hours) and checking for reimbursements on days they were there for a long period of time
# * Leveraging OCR data from receipts and grabbing their timestamps

# In[12]:

deputies = pd.read_csv('../data/2017-04-19-deputies.xz', low_memory=False)
print("Total deputies:", len(deputies))

sessions = pd.read_csv('../data/2017-04-19-session-start-times.xz', low_memory=False)
sessions['date'] = pd.to_datetime(sessions['date'], format="%Y-%m-%dT%H:%M:%S").dt.date
sessions['started_at'] = pd.to_datetime(sessions['started_at'], format="%Y-%m-%dT%H:%M:%S")
print("Session records:", len(sessions))

presences = pd.read_csv('../data/2017-04-19-presences.xz', low_memory=False)
presences['date'] = pd.to_datetime(presences['date'], format="%Y-%m-%dT%H:%M:%S").dt.date
presences.sort_values('date', ascending=False)
print("Presence records:", len(presences))

presences = presences.query('presence == "Present"')
print("Presence records with presence confirmed:", len(presences))

# Match presence with session and deputy info
presences = pd.merge(presences, sessions, on=['date', 'session'])
print("Presence records with session matched:", len(presences))

presences = pd.merge(deputies, presences, on='congressperson_document')
print("Presence records with deputies matched:", len(presences))


# In[13]:

presences['first_session_at'] = presences['started_at']
presences['last_session_at'] = presences['started_at']
presences['total_sessions'] = 0
aggregations = {
    'first_session_at': 'min',
    'last_session_at': 'max',
    'total_sessions': 'count',
    'session': lambda x: "{%s}" % ', '.join(x.astype(str)),
}
presences = presences.groupby(['congressperson_id', 'date'], as_index=False).agg(aggregations)
print("Confirmed presences grouped by date and congressperson:", len(presences))


# In[17]:

meals_outside_df = meals.query('company_state != "DF"')
meals_outside_df_while_in_df = pd.merge(
    left=presences, 
    right=meals_outside_df, 
    left_on=['congressperson_id', 'date'],
    right_on=['congressperson_id', 'issue_date']
)
print("Meals outside DF on days that the congressperson was there:", len(meals_outside_df_while_in_df))

meals_outside_df_while_in_df = meals_outside_df_while_in_df.query('company_name != "GOL LINHAS AEREAS S.A."')
print("Meals excluding expenses on flight:", len(meals_outside_df_while_in_df))

meals_outside_df_while_in_df = meals_outside_df_while_in_df[
    ~meals_outside_df_while_in_df.company_name.str.contains('HOTEL')
]
# We keep hotels out of the equation for this analysis since it they usually
# have meals made on multiple days. Not to say that the bill might dated from
# the day that the congressperson was back.
print("Meals excluding expenses on hotels:", len(meals_outside_df_while_in_df))


# In[18]:

def score(meal):
    return score_by_time(meal) + score_by_ts(meal)

def score_by_time(meal):
    if meal.total_sessions > 1:
        return meal.last_session_at.hour - meal.first_session_at.hour + (meal.total_sessions - 1)
    else:
        return 0
    
def score_by_ts(meal):
    if meal.timestamps == '':
        return 0
    
    occurences = 0
    for ts in meal.timestamps:
        if ts == None:
            continue
        if (meal.first_session_at.hour-1) < ts.tm_hour < (meal.last_session_at.hour+1):
            occurences += 1
    return occurences * 10
    
suspects = meals_outside_df_while_in_df.copy()
suspects.timestamps.fillna('', inplace=True)
suspects['score'] = suspects.apply(score, axis='columns')
suspects = suspects.query('score > 0').sort_values('score', ascending=False)
print("Suspicious reimbursements:", len(suspects))


# In[24]:

report(suspects.head(50), [
    'document_id',
    'receipt',
    'issue_date', 
    'congressperson_name',
    'company_name',
    'company_state', 
    'total_net_value',
    'score',
    'first_session_at', 
    'last_session_at',
])


# ## Meals outside DF while the congressperson was giving a speech
# 
# Like presence in sessions, we can identify suspicious reimbursements based on:
# * Making an approximation of the total time the congressperson was in Brasilia (like more than X hours) and checking for reimbursements on days they were there for a long period of time
# * Leveraging OCR data from receipts and grabbing their timestamps

# In[25]:

speeches = pd.read_csv('../data/2017-04-21-speeches.xz', low_memory=False)
print("Total speeches:", len(speeches))
# Clean up the data, see https://gist.github.com/fgrehm/bb0e1f6fef55082074d9a0258cf45391 for background
speeches = speeches[~speeches['speech_speaker_party'].isnull()]
speeches['speech_speaker_name'] = speeches['speech_speaker_name'].str.replace('\s+\(PRESIDENTE\)', '')
speeches['speech_speaker_party'] = speeches['speech_speaker_party'].str.upper()
speeches['speech_speaker_party'] = speeches['speech_speaker_party'].str.replace('PDSB', 'PSDB')
speeches['session_date'] = pd.to_datetime(speeches['session_date'], format="%Y-%m-%dT%H:%M:%S").dt.date
speeches['speech_started_at'] = pd.to_datetime(speeches['speech_started_at'], format="%Y-%m-%dT%H:%M:%S")
speeches = speeches[[
    'session_date',
    'speech_speaker_name', 
    'speech_speaker_party',
    'speech_speaker_state',
    'speech_started_at',
]]
print("Speeches by politicians:", len(speeches))


# In[26]:

speeches = pd.merge(
            speeches, 
            deputies, 
            left_on=['speech_speaker_name', 'speech_speaker_party', 'speech_speaker_state'],
            right_on=['congressperson_name', 'party', 'state'])
print("Speeches with matching deputy:", len(speeches))


# In[27]:

speeches['first_speech_at'] = speeches['speech_started_at']
speeches['last_speech_at'] = speeches['speech_started_at']
speeches['total_speeches'] = 0
aggregations = {
    'last_speech_at': 'max',
    'first_speech_at': 'min',
    'total_speeches': 'count',
}
speeches = speeches.groupby(['congressperson_document', 'session_date'], as_index=False).agg(aggregations)
print("Speeches grouped by date:", len(speeches))


# In[29]:

meals_outside_df_during_speeches = pd.merge(
    left=speeches, 
    right=meals_outside_df, 
    left_on=['congressperson_document', 'session_date'],
    right_on=['congressperson_document', 'issue_date']
)
print("Meals outside DF on days that the congressperson gave a speech:", len(meals_outside_df_during_speeches))

meals_outside_df_during_speeches = meals_outside_df_during_speeches.query('company_name != "GOL LINHAS AEREAS S.A."')
print("Meals excluding expenses on flight:", len(meals_outside_df_during_speeches))

meals_outside_df_during_speeches = meals_outside_df_during_speeches[
    ~meals_outside_df_during_speeches.company_name.str.contains('HOTEL')
]
print("Meals excluding expenses on hotels:", len(meals_outside_df_during_speeches))


# In[34]:

def score(meal):
    return score_by_time(meal) + score_by_ts(meal)

def score_by_time(meal):
    if meal.total_speeches > 1:
        return meal.first_speech_at.hour - meal.last_speech_at.hour + (meal.total_speeches - 1)
    else:
        return 0
    
def score_by_ts(meal):
    if meal.timestamps == '':
        return 0
    
    occurences = 0
    for ts in meal.timestamps:
        if ts == None:
            continue
        if (meal.first_speech_at.hour-1) < ts.tm_hour < (meal.last_speech_at.hour+1):
            occurences += 1
    return occurences * 10
    
suspects2 = meals_outside_df_during_speeches.copy()
suspects2.timestamps.fillna('', inplace=True)
suspects2['score'] = suspects2.apply(score, axis='columns')
suspects2 = suspects2.query('score > 0').sort_values('score', ascending=False)
print("Suspicious reimbursements:", len(suspects2))

suspects2 = suspects2[~suspects2.document_id.isin(suspects.document_id)]
print("Suspicious reimbursements that were not found using presences info:", len(suspects2))


# In[35]:

report(suspects2.head(20), [
    'document_id',
    'receipt',
    'issue_date', 
    'congressperson_name',
    'score',
    'company_state', 
    'total_net_value', 
    'first_speech_at', 
    'last_speech_at',
    'company_name'
])


# ## Meals in DF while the congressperson was outside DF
# 
# In the past we also found cases where the congressperson was on an official mission outside DF but requested a reimbursement for a meal in DF

# In[36]:

missions = pd.read_csv('../data/2017-04-19-official-missions.xz', low_memory=False)
missions.participant = missions.participant.apply(lambda x: x.upper())
missions.start = pd.to_datetime(missions.start, format="%Y-%m-%d").dt.date
missions.end = pd.to_datetime(missions.end, format="%Y-%m-%d").dt.date

print("Total official mission records:", len(missions))

missions = missions.merge(
    deputies, 
    left_on=['participant'],
    right_on=['congressperson_name']
)
print("Total official mission records with deputies:", len(missions))


# In[38]:

meals_in_df = meals.query('company_state == "DF"')
print("Meals in DF:", len(meals_in_df))


# In[39]:

suspects3 = []
for idx, mission in missions.iterrows():
    meals_while_in_mission = meals_in_df[
        (meals_in_df.issue_date >= (mission.start + timedelta(days=1))) \
        & (meals_in_df.issue_date <= (mission.end - timedelta(days=1))) \
        & (meals_in_df.congressperson_id == mission.congressperson_id)
    ]
    if (len(meals_while_in_mission) == 0):
        continue
    for _, m in meals_while_in_mission.iterrows():
        suspects3.append([
            m.document_id,
            m.applicant_id,
            m.year,
            m.issue_date,
            m.congressperson_name,
            m.total_net_value,
            m.company_state,
            m.company_name,
            "{}<br>{}<br><i>From '{}' to '{}'</i>".format(
                mission.destination,
                mission.subject,
                mission.start,
                mission.end
            )
        ])    
    
suspects3 = pd.DataFrame(suspects3, columns=[
    'document_id',
    'applicant_id',
    'year',
    'issue_date', 
    'congressperson_name',
    'total_net_value',
    'company_state', 
    'company_name',
    'mission'
])


# In[40]:

report(suspects3, [
    'document_id',
    'receipt',
    'issue_date', 
    'congressperson_name',
    'total_net_value', 
    'mission',
    'company_name',
    'company_state'
])

