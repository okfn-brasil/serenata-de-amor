import os
from datetime import date

import pandas as pd
import requests
from tqdm import tqdm

API_SERVER = 'http://compras.dados.gov.br'
API_ENDPOINT = API_SERVER + '/fornecedores/v1/fornecedores.json'


class Suppliers:

    def __init__(self):
        self.response = requests.get(API_ENDPOINT).json()
        self.total = self.response.get('count', 0)

    @property
    def next(self):
        path = self.response.get('_links', {}).get('next', {}).get('href')
        if path:
            return API_SERVER + path
        return False

    def pages(self):
        yield self.response
        while self.next:

            response = requests.get(self.next)
            if 200 <= response.status_code < 400:
                self.response = response.json()
                yield self.response

            else:
                msg = 'Server responded with a {} HTTP Status'
                print(msg.format(response.status_code))
                break

    def details(self):
        for page in self.pages():
            for supplier in page.get('_embedded', {}).get('fornecedores', []):
                yield supplier

    def fetch(self):
        with tqdm(total=self.total) as progress:
            for supplier in self.details():
                progress.update(1)
                yield supplier


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
        'habilitado_licitar': 'allowed_to_bid'
    }

    suppliers = Suppliers()
    df = pd.DataFrame(suppliers.fetch(), columns=columns)
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
