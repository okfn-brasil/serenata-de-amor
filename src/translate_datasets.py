import numpy as np
import pandas as pd
import sys

INPUT_FILE_PATH = sys.argv[1]
OUTPUT_FILE_PATH = INPUT_FILE_PATH \
    .replace('AnoAtual', 'current-year') \
    .replace('AnoAnterior', 'last-year') \
    .replace('AnosAnteriores', 'previous-years') \
    .replace('.csv', '.xz')

data = pd.read_csv(INPUT_FILE_PATH,
                   dtype={'ideDocumento': np.str,
                          'ideCadastro': np.str,
                          'nuCarteiraParlamentar': np.str,
                          'codLegislatura': np.str,
                          'txtCNPJCPF': np.str,
                          'numRessarcimento': np.str})
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

data['subquota_description'] = data['subquota_description'].astype('category')
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

data.to_csv(OUTPUT_FILE_PATH,
            compression='xz',
            index=False)
