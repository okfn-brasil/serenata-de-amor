import os
import time
import requests
import pandas as pd


SUPPLIERS_PURCHASE_ENDPOINT = 'http://compras.dados.gov.br/fornecedores/v1/fornecedores.json'


def fetch_suppliers():
    print('Loading first results...')
    response = requests.get(SUPPLIERS_PURCHASE_ENDPOINT).json()
    yield response

    last_page = response['count']
    for page in range(2, last_page):
        print('{}/{}'.format(page, last_page))
        response = requests.get(SUPPLIERS_PURCHASE_ENDPOINT).json()
        yield response


def retrieve_data():
    suppliers_attributes_columns = {
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

    suppliers_info = []

    for suppliers_page in fetch_suppliers():
        for supplier in suppliers_page['_embedded']['fornecedores']:
            suppliers_info.append(supplier)

    df = pd.DataFrame(suppliers_info, columns=suppliers_attributes_columns.keys())
    df.rename(columns=dict(zip(suppliers_attributes_columns.keys(), suppliers_attributes_columns.values())), inplace=True)

    return df


def save_csv(df):
    dataset_name = time.strftime('%Y-%m-%d') + '-' + 'purchases-suppliers.xz'
    df.to_csv(path_or_buf=os.path.join('data', dataset_name), sep=',', compression='xz', encoding='utf-8', index=False)


def main():
    suppliers_info = retrieve_data()
    save_csv(suppliers_info)


if __name__ == '__main__':
    main()
