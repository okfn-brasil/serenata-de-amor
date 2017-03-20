import os
from datetime import date

import pandas as pd
import requests


SUPPLIERS_PURCHASE_ENDPOINT = (
    'http://compras.dados.gov.br/'
    'fornecedores/v1/fornecedores.json'
)


def supplier_pages():
    print('Loading first results...')
    response = requests.get(SUPPLIERS_PURCHASE_ENDPOINT).json()
    yield response

    last_page = response['count']
    for page in range(2, last_page):
        print('{}/{}'.format(page, last_page))
        response = requests.get(SUPPLIERS_PURCHASE_ENDPOINT).json()
        yield response


def supplier_details():
    for page in supplier_pages():
        yield from page.get('_embedded', {}).get('fornecedores', [])


def retrieve_data():
    columns = {
        'id': 'id',
        'cnpj': 'cnpj',
        'nome': 'name',
        'ativo': 'active',
        'recadastrado': 'relisted',
        'id_municipio': 'city_id',
        'uf': 'state',
        'id_natureza_juridica': 'legal_nature_id',
        'id_porte_empresa': 'company_size_id',
        'id_ramo_negocio': 'business_id',
        'id_unidade_cadastradora': 'responsible_entity',
        'id_cnae': 'cnae_id',
        'habilitado_licitar': 'allowed_to_bid'}

    suppliers = supplier_details()
    df = pd.DataFrame(suppliers, columns=columns)
    df.rename(columns=columns, inplace=True)

    return df


def save_csv(df):
    dataset_name = date.today().strftime('%Y-%m-%d') + '-purchase-suppliers.xz'
    dataset_path = os.path.join('data', dataset_name)
    df.to_csv(dataset_path, compression='xz', encoding='utf-8', index=False)


def main():
    suppliers = retrieve_data()
    save_csv(suppliers)


if __name__ == '__main__':
    main()
