import itertools
import json
import os
from datetime import date

import numpy as np
import pandas as pd
import requests
from geopy.geocoders import GoogleV3

HTTP_HEADERS = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.102 Safari/537.36"}
FILENAME = '{}-real-estates-prices.xz'.format(date.today())
OUTPUT_FILEPATH = os.path.join('data', FILENAME)
locations = ['Distrito Federal, Brasil', ]

def slice_quadrants(location_bounds, size=0.05):
    northeast = location_bounds['northeast']
    southwest = location_bounds['southwest']

    for lat in np.arange(southwest['lat'], northeast['lat'], size):
        for long in np.arange(southwest['lng'], northeast['lng'], size):
            yield ((str(lat), str(long)), (str(lat + size), str(long + size)))

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
        log_percent(i+1)

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

def log_percent(done, total=None, msg='Fetched {} out of {} ({:.2f}%)'):
    if total:
        print(msg.format(done, total, done/total*100), end='\r')
    else:
        msg = 'Fetched {}'
        print(msg.format(done), end='\r')

def get_quadrants():
    geolocator = GoogleV3()
    quadrant_generators = []
    for location in locations:
        location_bounds = geolocator.geocode(location).raw['geometry']['bounds']
        quadrant_generators.append(slice_quadrants(location_bounds))

    return itertools.chain(*quadrant_generators)

def main():
    quadrants = get_quadrants()
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
    cleaned_data.to_csv(OUTPUT_FILEPATH, compression='xz')

if __name__ == '__main__':
    main()
