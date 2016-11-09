import configparser
import math
import os
import pickle
import re
import shutil
from concurrent import futures
from warnings import warn

import pandas as pd
import requests
from geopy.distance import vincenty

OUTPUT = os.path.join('data', 'suspicious_distances.xz')
TEMP_PATH = os.path.join('data', 'tmp_suspect_search')
CNPJ_REGEX = r'[./-]'

settings = configparser.RawConfigParser()
settings.read('config.ini')


class SuspectPlaceSearch:

    BASE_URL = 'https://maps.googleapis.com/maps/api/place/'
    DETAILS_URL = BASE_URL + 'details/json?placeid={}&key={}'
    NEARBY_URL = BASE_URL + 'nearbysearch/json?location={}&keyword={}&rankby=distance&key={}'

    def __init__(self, key):
        self.GOOGLE_API_KEY = key

    def find_places(self, lat, lng, keywords):
        """
        :param lat: (float) latitude
        :param lng: (float) longitude
        :param keyworks: (iterable) list of keywords
        """
        for keyword in keywords:

            # Create the request for the Nearby Search Api. The Parameter
            # rankby=distance will return a ordered list by distance
            latlong = '{},{}'.format(lat, lng)
            url = self.NEARBY_URL.format(latlong, keyword, self.GOOGLE_API_KEY)
            nearby = requests.get(url).json()

            # TODO: create distincts messages erros for the api results
            if nearby['status'] != 'OK':
                if 'error_message' in nearby:
                    msg = 'GooglePlacesAPIException: {}: {}'
                    warn(msg.format(nearby['status'], nearby['error_message']))
                else:
                    msg = 'GooglePlacesAPIException: {}'
                    warn(msg.format(nearby['status']))

            # If have some result for this keywork, get first
            else:
                place = nearby['results'][0]
                latitude = float(place.get('geometry').get('location').get('lat'))
                longitude = float(place.get('geometry').get('location').get('lng'))
                distance = vincenty((lat, lng), (latitude, longitude)).meters
                suspicious_place = {
                    'id': place.get('place_id'),
                    'keyword': keyword,
                    'latitude': latitude,
                    'longitude': longitude,
                    'distance': distance
                }
                yield suspicious_place

    def place_details(self, place):
        """
        :param place: dictonary with id key.
        :return: dictionary updated with name, address and phone.
        """
        url = self.DETAILS_URL.format(place['id'], self.GOOGLE_API_KEY)
        details = requests.get(url).json()
        place['name'] = details['result']['name']
        place['address'] = details['result'].get('formatted_address', '')
        place['phone'] = details['result'].get('formatted_phone_number', '')
        return place

    def search(self, lat, lng):
        """
        Return a dictonary containt information of a
        suspect place arround a given position.
        A suspect place is some company that match a suspect keyword
        in a Google Places search.

        :param lat: latitude
        :param lng: longitude
        :return: closest_suspect_place, a dict with the keys:
            - name : The name of suspect place
            - latitude : The latitude of suspect place
            - longitude : The longitude of suspect place
            - distance : The distance in meters between suspect place and the given lat, lng
            - address : The address  of suspect place
            - phone : The phone of suspect place
            - id : The Google Place ID of suspect place
            - keyword : The Keyword that generate the place
                        in Google Place Search
        """
        keywords = ('Acompanhantes',
                    'Adult Entertainment Club',
                    'Adult Entertainment Store',
                    'Gay Sauna',
                    'Massagem',
                    'Modeling Agency',
                    'Motel',
                    'Night Club',
                    'Sex Club',
                    'Sex Shop',
                    'Strip Club',
                    'Swinger clubs')

        # for a case of nan in parameters
        lat, lng = float(lat), float(lng)
        if math.isnan(lat) or math.isnan(lng):
            return None

        # Get the closest place inside all the searched keywords
        suspicious_places = self.find_places(lat, lng, keywords)
        try:
            closest_place = min(suspicious_places, key=lambda x: x['distance'])
        except ValueError:
            return None  # i.e, not suspect place found around

        return self.place_details(closest_place)

def search_suspect_around_companies(companies):
    with futures.ThreadPoolExecutor(max_workers=40) as executor:
        future_to_search_suspects = dict()
        for index, company in companies.iterrows():
            future = executor.submit(search_suspect_around_company, company)
            future_to_search_suspects[future] = company
        for future in futures.as_completed(future_to_search_suspects):
            company = future_to_search_suspects[future]
            if future.exception() is not None:
                print('%r raised an exception: %s' % (company['cnpj'],
                                                      future.exception()))
            elif future.result() is not None:
                write_suspects_info(future.result(), company['cnpj'])


def search_suspect_around_company(company):

    latitude = company["latitude"]
    longitude = company['longitude']
    geolocation = "{},{}".format(latitude, longitude)
    if geolocation == '':
        print('No geolocation information for ', company[
              'name'], company['cnpj'],
              ' is impossible to search suspects around')
        return None
    else:
        try:
            sp = SuspectPlaceSearch(settings.get('Google', 'APIKey'))
            suspect = sp.search(lat=latitude, lng=longitude)
        except ValueError as e:
            print(e)
            return None
        return suspect


def write_suspects_info(suspect_around, cnpj):
    cnpj = re.sub(CNPJ_REGEX, '', cnpj)
    print('Writing %s' % cnpj)
    with open('%s/%s.pkl' % (TEMP_PATH, cnpj), 'wb') as f:
        pickle.dump(suspect_around, f, pickle.HIGHEST_PROTOCOL)


def read_suspect_info(company):
    cnpj = re.sub(CNPJ_REGEX, '', company['cnpj'])
    filename = '%s/%s.pkl' % (TEMP_PATH, cnpj)
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            try:
                suspect_place = pickle.load(f)
            except (ValueError, EOFError) as e:
                return pd.Series()
        if suspect_place is None:
            return pd.Series()
        else:
            return pd.Series({'suspect_place_around': suspect_place['name'],
                              'distance_to_suspect': suspect_place['distance'],
                              'suspect_phone': suspect_place['phone'],
                              'suspect_latitude': suspect_place['latitude'],
                              'suspect_longitude': suspect_place['longitude'],
                              })
    else:
        return pd.Series()


def get_companies_path():
    regex = r'^[\d-]{11}companies.xz$'
    for file_name in os.listdir('data'):
        if re.compile(regex).match(file_name):
            return os.path.join('data', file_name)


if __name__ == '__main__':

    if not os.path.exists(TEMP_PATH):
        os.makedirs(TEMP_PATH)

    data = pd.read_csv(get_companies_path(), low_memory=False)

    searched_for_suspects_cnpjs = [filename[:14]
                                for filename in os.listdir(TEMP_PATH)
                                if filename.endswith('.pkl')]

    is_not_searched_for_suspects = ~data['cnpj'].str.replace(
        CNPJ_REGEX, '').isin(searched_for_suspects_cnpjs)

    remaining_companies = data[is_not_searched_for_suspects]

    print('%i companies, %i to go' % (len(data), len(remaining_companies)))

    search_suspect_around_companies(remaining_companies)

    data = pd.concat([data, data.apply(read_suspect_info, axis=1)], axis=1)

    data.to_csv(OUTPUT, compression='xz', encoding='utf-8', index=False)

    shutil.rmtree(TEMP_PATH)
