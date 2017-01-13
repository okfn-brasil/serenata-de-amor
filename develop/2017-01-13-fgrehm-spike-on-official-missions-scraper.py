
# coding: utf-8

# # Spike on official missions scraper
# 
# We've sucessfully identified lots of suspicious meal reimbursements using information about congress people presence in congress sessions in Brasília and by using the data available at http://www.camara.leg.br/missao-oficial/index.jsp we can easily identify a period of time that a congress person was in a given city in Brazil or country. This notebook outlines a spike on scrapping its information and present some insights about the data available and how to use it.

# In[1]:

import os
import re
import urllib

from datetime import timedelta

import pandas as pd
import numpy as np

from bs4 import BeautifulSoup

URL = (
    'http://www.camara.leg.br/missao-oficial/missao-pesquisa?'
    'deputado=1&'
    'nome-deputado=&'
    'nome-servidor=&'
    'dati={0}&'
    'datf={1}&'
    'nome-evento='
)

def translate_column(df, column, translations):
    df[column] = df[column].astype('category')
    translations = [translations[cat]
                   for cat in df[column].cat.categories]

    df[column].cat.rename_categories(translations,
                                     inplace=True)


# Notes about the logic below:
#     
# - The form allow us to either search for all missions from all deputies but it restricts the date range to 90 days
# - While we could search for longer ranges by providing the congress person name, its easier to get the data for all of them in one shot
# - To make things easier, we create a lot of 2 months slices given that missions usually takes less than a month.
# - Those slices have a 1 month overlap because the date range searched needs to include all of the dates that makes up for the mission. For example, if instead we provided consecutive 1 month slices, a session that took place by the end of one month and lasted until the beggining of the next one would not be returned

# In[2]:

# REFACTOR: Make the code below a generator

ranges = [
    ['01/02/2015', '01/04/2015'],
    ['01/03/2015', '01/05/2015'],
    ['01/04/2015', '01/06/2015'],
    ['01/05/2015', '01/07/2015'],
    ['01/06/2015', '01/08/2015'],
    ['01/07/2015', '01/09/2015'],
    ['01/08/2015', '01/10/2015'],
    ['01/09/2015', '01/11/2015'],
    ['01/10/2015', '01/12/2015'],
    ['01/11/2015', '01/01/2016'],
    ['01/12/2015', '01/02/2016'],
    ['01/01/2016', '01/03/2016'],
    ['01/02/2016', '01/04/2016'],
    ['01/03/2016', '01/05/2016'],
    ['01/04/2016', '01/06/2016'],
    ['01/05/2016', '01/07/2016'],
    ['01/06/2016', '01/08/2016'],
    ['01/07/2016', '01/09/2016'],
    ['01/08/2016', '01/10/2016'],
    ['01/09/2016', '01/11/2016'],
    ['01/10/2016', '01/12/2016'],
    ['01/11/2016', '01/01/2017'],
    ['01/12/2016', '01/02/2017'],
]

records = []
for r in ranges:
    print(r)
    url = URL.format(r[0], r[1])
    data = urllib.request.urlopen(url)
    soup = BeautifulSoup(data, 'html.parser')
    
    table = soup.findAll('tbody', attrs={'class': 'coresAlternadas'})[0]
    for row in table.find_all('tr', recursive=False):
        cells = row.findAll('td')
        start = cells[0].text.strip()
        end = cells[1].text.strip()
        subject = cells[2].text.strip()
        destination = cells[3].text.strip()
        participant = cells[4].find('span').text.strip()
        report_status = cells[4].find('a')
        report_details_link = None
        if report_status == None:
            report_status = cells[4].find_all('td')[1].text.strip()
        else:
            report_details_link = "http://www.camara.leg.br" + report_status['href'].strip().replace("\r\n", '').replace("\t", '')
            report_status = report_status.text.strip()
        records.append([
            participant,
            destination,
            subject,
            start,
            end,
            report_status,
            report_details_link
        ])
        
raw_missions = pd.DataFrame(records, columns=[
    'participant',
    'destination',
    'subject', 
    'start',
    'end',
    'report_status',
    'report_details_link'
])

translate_column(raw_missions, 'report_status', {
    'Disponível': 'Available',
    'Pendente': 'Pending',
    'Em análise': 'Analysing'
})


# Because we provide overlapping ranges, there are lots of duplicated missions so we gotta clean up the dataset to reduce the noise

# In[3]:

missions = raw_missions.drop_duplicates()
print(len(raw_missions))
print(len(missions))
missions.head(5)


# ## Matching missions with deputies
# 
# By matching the missions and deputies dataset we can grab the congressperson information for matching with reimbursements and other datasets we have around but we need to do some changes to the data.

# In[4]:

deputies = pd.read_csv('../data/2016-12-21-deputies.xz', low_memory=False)
print(len(pd.merge(
    missions,
    deputies, 
#   how='left', 
    left_on=['participant'],
    right_on=['name']
)))


# Direct matching is not possible and the reason behind that is that the name on the deputies dataset is uppercased

# In[5]:

missions['name'] = missions.participant.apply(lambda x: x.upper())
data = pd.merge(
    missions,
    deputies,
    how='left',
    left_on=['name'],
    right_on=['name']
)
print(len(data))
print(len(data[data.congressperson_id.isnull()]))


# We still don't get all the missions to match 100%

# In[6]:

data[data.congressperson_id.isnull()].name.unique()


# These are probably deputies that are no longer around since as we can see Eduardo Cunha is on the list

# ## Where have people gone?

# In[7]:

print(len(data.destination.unique()))
data.destination.unique()


# Apparently we can identify cities in Brasil by searching for the `/` char

# In[8]:

in_br = data[data.destination.str.contains('/')]
print(len(in_br.destination.unique()))
in_br.destination.value_counts()


# And just negate that for missions abroad:

# In[9]:

abroad = data[~data.destination.str.contains('/')]
print(len(abroad.destination.unique()))
abroad.destination.value_counts()


# ## Reimbursements while in a mission

# In[10]:

reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz', dtype={'cnpj_cpf': np.str}, low_memory=False)
print("Total:", len(reimbursements))
reimbursements = reimbursements.query("year >= 2015")
print(">= 2015:", len(reimbursements))
reimbursements = reimbursements.query("subquota_description == 'Congressperson meal'")
reimbursements['issue_date'] = pd.to_datetime(reimbursements['issue_date'], format="%Y-%m-%dT%H:%M:%S").dt.date
print("Meals:", len(reimbursements))


# In[11]:

data['start'] = pd.to_datetime(data['start'], format="%Y-%m-%d").dt.date
data['end'] = pd.to_datetime(data['end'], format="%Y-%m-%d").dt.date

count = 0
net_val = 0
count_abroad = 0
net_val_abroad = 0
count_abroad_br = 0
net_val_abroad_br = 0

for _, m in data.iterrows():
    matches = reimbursements[
        (reimbursements.issue_date >= (m.start + timedelta(days=1))) \
        & (reimbursements.issue_date <= (m.end - timedelta(days=1))) \
        & (reimbursements.congressperson_id == m.congressperson_id)
    ]
    if (len(matches) == 0):
        continue
    count += len(matches)
    
    mission_abroad = ('/' not in m.destination)
    if mission_abroad:
        count_abroad += len(matches)
    
    for _, r in matches.iterrows():
        net_val += r.total_net_value
        if mission_abroad:
            net_val_abroad += r.total_net_value
            if r.document_type != 2:
                count_abroad_br += 1
                net_val_abroad_br += r.total_net_value

print(count, "reimbursements found for congressperson while in a mission summing R$", net_val)
print(count_abroad, "reimbursements found for congressperson while in a mission abroad summing R$", net_val_abroad)
print(count_abroad_br, "reimbursements in Brasil found for congressperson while in a mission abroad summing R$", net_val_abroad_br)


# ## Conclusion / next steps
# 
# - I'll investigate those reimbursements in Brasil found for congressperson while in a mission abroad and will look into reporting the suspicious ones
# - I've got a WIP on top of the work done on [serenata-toolbox#17](https://github.com/datasciencebr/serenata-toolbox/pull/17) that identifies the dates when deputies are on official missions and some preliminary manual analysis I made shows that we have lots of deputies that were supposed to be on official missions but have no associated data on the missions dataset, we could gather the numbers and put up a formal inquiry about the missing data if the number is really significant since deputies are expected to provide a report 15 days after returning from a mission
# - In order to work around the above and once we have some infrastructure in place for OCRing documents, we could try searching for deputies names on reports provided by one of the deputies. (for ex, the [report](http://www.camara.leg.br/missao-oficial/missao_oficial_Relatorio?codViagem=49774&ponto=811886) provided on the [report details](http://www.camara.leg.br/missao-oficial/missao-relatorio?codViagem=49774&ponto=811886) linked on the official missions dataset contains the name of other deputies that went on that mission)
