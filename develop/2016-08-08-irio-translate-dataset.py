
# coding: utf-8

# # Translate dataset
# 
# The main language of the project is English: works well mixed in programming languages like Python and provides a low barrier for non-Brazilian contributors. Today, the dataset we make available by default for them is a set of XMLs from The Chamber of Deputies, in Portuguese. We need attribute names and categorical values to be translated to English.
# 
# This file is intended to serve as a base for the script to translate current and future datasets in the same format.

# In[1]:

import pandas as pd

data = pd.read_csv('../data/2016-08-08-AnoAtual.csv')
data.shape


# In[2]:

data.head()


# In[3]:

data.iloc[0]


# New names are based on the "**Nome do Dado**" column of the table available at [`data/2016-08-08-datasets-format.html`](http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/explicacoes-sobre-o-formato-dos-arquivos-xml), not "**Elemento de Dado**", their current names.

# In[4]:

data.rename(columns={
        'ideDocumento': 'document_id',
        'txNomeParlamentar': 'congressperson_name',
        'ideCadastro': 'congressperson_id',
        'nuCarteiraParlamentar': 'congressperson_document',
        'nuLegislatura': 'term',
        'sgUF': 'state',
        'sgPartido': 'party',
        'codLegislatura': 'term_id',
        'numSubCota': 'subquota_number',
        'txtDescricao': 'subquota_description',
        'numEspecificacaoSubCota': 'subquota_group_id',
        'txtDescricaoEspecificacao': 'subquota_group_description',
        'txtFornecedor': 'supplier',
        'txtCNPJCPF': 'cnpj_cpf',
        'txtNumero': 'document_number',
        'indTipoDocumento': 'document_type',
        'datEmissao': 'issue_date',
        'vlrDocumento': 'document_value',
        'vlrGlosa': 'remark_value',
        'vlrLiquido': 'net_value',
        'numMes': 'month',
        'numAno': 'year',
        'numParcela': 'installment',
        'txtPassageiro': 'passenger',
        'txtTrecho': 'leg_of_the_trip',
        'numLote': 'batch_number',
        'numRessarcimento': 'reimbursement_number',
        'vlrRestituicao': 'reimbursement_value',
        'nuDeputadoId': 'applicant_id',
    }, inplace=True)


# In[5]:

data['subquota_description'] = data['subquota_description'].astype('category')
data['subquota_description'].cat.categories


# When localizing categorical values, I prefer a direct translation over adaptation as much as possible. Not sure what values each attribute will contain, so I give the power of the interpretation to the people analyzing it in the future.

# In[6]:

data['subquota_description'].cat.rename_categories([
        'Publication subscriptions',
        'Fuels and lubricants',
        'Consultancy, research and technical work',
        'Publicity of parliamentary activity',
        'Flight ticket issue',
        'Congressperson meal',
        'Lodging, except for congressperson from Distrito Federal',
        'Aircraft renting or charter of aircraft',
        'Watercraft renting or charter',
        'Automotive vehicle renting or charter',
        'Maintenance of office supporting parliamentary activity',
        'Participation in course, talk or similar event',
        'Flight tickets',
        'Terrestrial, maritime and fluvial tickets',
        'Security service provided by specialized company',
        'Taxi, toll and parking',
        'Postal services',
        'Telecommunication',
    ], inplace=True)


# In[7]:

data.head()


# In[8]:

data.iloc[0]


# In[ ]:



