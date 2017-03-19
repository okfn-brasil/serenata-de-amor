import os
import requests
import pandas as pd


def fetch_suppliers():
    raw_suppliers = []
    response = requests.get('http://compras.dados.gov.br/fornecedores/v1/fornecedores.json').json()
    raw_suppliers = raw_suppliers + response['_embedded']['fornecedores']

    last_page = response['count']
    for page in range(2, last_page):
        print('{}/{}'.format(page, last_page))
        response = requests.get('http://compras.dados.gov.br/fornecedores/v1/fornecedores.json').json()
        raw_suppliers = raw_suppliers + response['_embedded']['fornecedores']
    return raw_suppliers


def prepare_data(raw_data):
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

    df = pd.DataFrame(raw_data, columns = suppliers_attributes_columns.keys())

    return df


def save_csv(df):
    df.to_csv(path_or_buf=os.path.join('data', 'purchase_suppliers.xz'), sep=',', compression='xz', encoding='utf-8', index=False)

def main():
    raw_data = fetch_suppliers()
    suppliers_info = prepare_data(raw_data)
    save_csv(suppliers_info)

if __name__ == '__main__':
    main()
