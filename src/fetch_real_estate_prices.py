import json
import numpy as np
import requests
import os
import pandas as pd
from geopy.geocoders import GoogleV3

HTTP_HEADERS = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.102 Safari/537.36"}
OUTPUT_FILEPATH = os.path.join('data', 'real_estates_prices.csv')
LOCATION = 'Distrito Federal, Brasil'

def slice_quadrants(northeast, southwest, size=0.0625):
    quadrants = []
    for lat in np.arange(southwest['lat'], northeast['lat'], size):
        for long in np.arange(southwest['lng'], northeast['lng'], size):
            quadrant = ((str(lat), str(long)), (str(lat + size), str(long + size)))
            quadrants.append(quadrant)
    return quadrants

def get_real_estates_from_quadrants(quadrants):
    estates = []
    url = 'http://www.zapimoveis.com.br/BuscaMapa/ObterOfertasBuscaMapa/'
    for i, quadrant in enumerate(quadrants):
        search_params = {
            "CoordenadasAtuais": {
                "Latitude": -15.7217174,
                "Longitude": -48.0783226
            },
            "CoordenadasMinimas": {
                "Latitude": quadrant[0][0],
                "Longitude": quadrant[0][1]
            },
            "CoordenadasMaximas": {
                "Latitude": quadrant[1][0],
                "Longitude": quadrant[1][1]
            },
            "Transacao": "Locacao",
            "TipoOferta":"Imovel"
        }

        results = get_results(url, {'parametrosBusca': str(search_params)})
        print_not_fetched_amount(results)
        estates.extend(results.get('Imoveis'))
        log_percent(i+1, len(quadrants))

    print('\nFetched {} real estates.'.format(len(estates)))

    return estates

def get_real_estates_details(real_estates):
    details = []
    all_ids = [e['ID'] for e in real_estates]
    url = 'http://www.zapimoveis.com.br/BuscaMapa/ObterDetalheImoveisMapa/'
    ids_per_request = 10
    total = len(all_ids)

    splitted_ids = [all_ids[x:x+ids_per_request] for x in range(0, total, ids_per_request)]

    for i, ids in enumerate(splitted_ids):
        results = get_results(url, {'listIdImovel': str(ids)})
        details.extend(results)

        log_percent(i*len(results)+1, total)

    print('\nFetched {} real estates details.'.format(len(details)))

    return details

def get_results(url, data, headers=HTTP_HEADERS):
    request = requests.post(url, headers=headers, data=data)
    estates_data = json.loads(request.text)
    return estates_data.get('Resultado')

def print_not_fetched_amount(results):
    if not results:
        return
    not_fetched_amount = results.get('QuantidadeResultados') - 1000
    if not_fetched_amount > 0:
        print('{} results aren\'t being fetched, decrease the quadrant size to get more results'.format(not_fetched_amount))

def log_percent(done, total, msg='Fetched {} out of {} ({:.2f}%)'):
    print(msg.format(done, total, done/total*100), end='\r')

def main():
    location = GoogleV3().geocode(LOCATION)
    location_bounds = location.raw['geometry']['bounds']

    quadrants = slice_quadrants(location_bounds['northeast'], location_bounds['southwest'])
    real_estates = get_real_estates_from_quadrants(quadrants)
    real_estates_details = get_real_estates_details(real_estates)

    real_estates_data = pd.DataFrame.from_dict(real_estates).set_index('ID')
    real_estates_details_data = pd.DataFrame.from_dict(real_estates_details).set_index('ID')

    joined = real_estates_data.join(real_estates_details_data, how='inner', rsuffix='_details')

    cleaned_data = joined\
                    .dropna(axis=1, how='all')\
                    .drop(['PrecoVenda_details',
                           'PrecoLocacao_details',
                           'TipoOfertaID_details',
                           'TipoOfertaID',
                           'indOferta',
                           'EstagioObra',
                           'FotoPrincipal',
                           'IndDistrato',
                           'SubTipoOferta'],
                          1)\
                    .rename(columns={
                        'Coordenadas': 'coordinates',
                        'NotaLocacao': 'rent_rate',
                        'NotaVenda': 'sale_rate',
                        'PrecoLocacao': 'rental_price',
                        'PrecoVenda': 'sale_price',
                        'AreaTotal': 'total_area' ,
                        'AreaUtil_details': 'useful_area',
                        'Bairro': 'neighborhood',
                        'Dormitorios_details': 'dorms',
                        'SubTipoImovel': 'subtype',
                        'Suites': 'suite',
                        'Vagas': 'vacancies',
                    })
    cleaned_data.to_csv(OUTPUT_FILEPATH)

if __name__ == '__main__':
    main()
