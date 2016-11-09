import configparser
import math
import os
import re
import lzma
import csv
import datetime
from concurrent import futures
from warnings import warn
from io import StringIO

import pandas as pd
import requests
from geopy.distance import vincenty

DATE = datetime.date.today().strftime('%Y-%m-%d')
OUTPUT = os.path.join('data', '{}-suspicious_distances.xz'.format(DATE))
TEMP_PATH = os.path.join('data', 'tmp_suspect_search')

settings = configparser.RawConfigParser()
settings.read('config.ini')


class SuspiciousPlaceSearch:

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

def search_suspicious_around_companies(companies):
    """
    :param companies: pandas dataframe.
    """
    with futures.ThreadPoolExecutor(max_workers=40) as executor:
        future_to_search_suspicious = dict()
        for index, company in companies.iterrows():
            future = executor.submit(search_suspicious_around_company, company)
            future_to_search_suspicious[future] = company
        for future in futures.as_completed(future_to_search_suspects):
            company = future_to_search_suspicious[future]
            if future.exception() is not None:
                warn('{} raised an exception: {}'.format(company['cnpj'],
                                                      future.exception()))
            elif future.result() is not None:
                write_suspicious_info(future.result(), company['cnpj'])


def search_suspicious_around_company(company):
    """
    :param company: panda series.
    :return: suspect
    """
    latitude = company["latitude"]
    longitude = company['longitude']
    geolocation = "{},{}".format(latitude, longitude)
    if not geolocation:
        warn('No geolocation information for company: {} ({})'
            .format(company['name'], company['cnpj']))
        return None

    sp = SuspiciousPlaceSearch(settings.get('Google', 'APIKey'))
    suspicious = sp.search(lat=latitude, lng=longitude)
    return suspicious


def write_suspicious_info(suspect_around, cnpj):
    cnpj = ''.join(re.findall(r'[\d]', cnpj))
    print('Writing {}'.format(cnpj))
    write_csv(suspect_around.update({'cnpj': cnpj}))


def write_csv(company=None):
    csv_io = StringIO()
    fieldnames = ['id', 'keyword', 'latitude', 'longitude', 'distance', 'name',
            'address', 'phone', 'cnpj']
    writer = csv.DictWriter(csv_io, fieldnames=fieldnames)
    if company:
        writer.writerow(company)
    else:
        writer.writeheader()
    with lzma.open(OUTPUT, 'at') as output:
        print(csv_io.getvalue(), file=output)
    csv_io.close()

def get_companies_path():
    regex = r'^[\d-]{11}companies.xz$'
    for file_name in os.listdir('data'):
        if re.compile(regex).match(file_name):
            return os.path.join('data', file_name)


if __name__ == '__main__':

    write_csv()

    data = pd.read_csv(get_companies_path(), low_memory=False)

    print('{} companies'.format(len(data)))

    search_suspicious_around_companies(data)
