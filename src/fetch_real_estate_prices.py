## juntar todos os IDs retornados e pegar os detalhes de cada imovel

## import geocoder

## def main():
##     geo_location = geocoder.google("Distrito Federal, Brasil")
##     location_boundingbox = geolocation.bbox
import numpy as np
import json
import requests

HEADERS = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.102 Safari/537.36"}

def slice_quadrants(northeast, southwest, size=0.0625):
    quadrants = []
    for lat in np.arange(southwest[0], northeast[0], size):
        for long in np.arange(southwest[1], northeast[1], size):
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

        if results:
            results_not_fetched_amount = results.get('QuantidadeResultados') - 1000
            if results_not_fetched_amount > 0:
                print('{} results aren\'t being fetched, decrease the quadrant size to get more results'.format(results_not_fetched_amount))
            estates.extend(results.get('Imoveis'))
        print('Fetched {} out of {} ({:.2f}%)'.format(i+1, len(quadrants), (i+1) / len(quadrants) * 100), end='\r')
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

        ids_fetched = i*len(results)+1
        print('Fetched {} out of {} ({:.2f}%)'.format(ids_fetched, total, ids_fetched/total*100), end='\r')
    print('\nFetched {} real estates details.'.format(len(details)))

    return details

def get_results(url, data, headers=HEADERS):
    request = requests.post(url, headers=HEADERS, data=data)
    estates_data = json.loads(request.text)
    return estates_data.get('Resultado')

if __name__ == '__main__':
    from unittest import TestCase

    t = TestCase()
    northeast, southwest = [-15, -47], [-16, -48]
    size = 0.125

    t.assertEqual(type(slice_quadrants(northeast, southwest)), list)
    t.assertEqual(type(slice_quadrants(northeast, southwest)[0]), tuple)
    t.assertEqual(slice_quadrants(northeast, southwest, size)[0], (('-16.0', '-48.0'),('-15.875','-47.875')))
    t.assertEqual(slice_quadrants(northeast, southwest, size)[1], (('-16.0', '-47.875'),('-15.875','-47.75')))
    t.assertEqual(slice_quadrants(northeast, southwest, size)[8], (('-15.875', '-48.0'),('-15.75','-47.875')))
    t.assertEqual(slice_quadrants(northeast, southwest, size)[-1], (('-15.125', '-47.125'),('-15.0','-47.0')))

    bbox = {'northeast': [-15.5001711, -47.3081926],
           'southwest': [-16.0517623, -48.2870948]}

    get_real_estates_details(get_real_estates_from_quadrants(slice_quadrants(bbox['northeast'], bbox['southwest'])))
