import configparser
import csv
import datetime
import lzma
import math
import os
import re
from io import StringIO
from multiprocessing import Pool
from shutil import copyfile

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

    def find_places(self, company, keywords):
        """
        :param company: (dict) with latitude and longitude keys (as floats)
        :param keyworks: (iterable) list of keywords
        """
        for keyword in keywords:

            # Create the request for the Nearby Search Api. The Parameter
            # rankby=distance will return a ordered list by distance
            lat, lng = company['latitude'], company['longitude']
            latlong = '{},{}'.format(lat, lng)
            url = self.NEARBY_URL.format(latlong, keyword, self.GOOGLE_API_KEY)
            nearby = requests.get(url).json()

            if nearby['status'] != 'OK':
                if 'error_message' in nearby:
                    print('{}: {}'.format(nearby.get('status'),
                                          nearby.get('error_message')))
                elif nearby.get('status') != 'ZERO_RESULTS':
                    msg = 'Google Places API Status: {}'
                    print(msg.format(nearby.get('status')))

            # If have some result for this keywork, get first
            else:
                try:
                    place = nearby.get('results')[0]
                    location = place.get('geometry').get('location')
                    latitude = float(location.get('lat'))
                    longitude = float(location.get('lng'))
                    distance = vincenty((lat, lng), (latitude, longitude))
                    yield {
                        'id': place.get('place_id'),
                        'keyword': keyword,
                        'latitude': latitude,
                        'longitude': longitude,
                        'distance': distance.meters,
                        'cnpj': company.get('cnpj')
                    }
                except TypeError:
                    pass

    def place_details(self, place):
        """
        :param place: dictonary with id key.
        :return: dictionary updated with name, address and phone.
        """
        url = self.DETAILS_URL.format(place.get('id'), self.GOOGLE_API_KEY)
        details = requests.get(url).json()
        place.update({
            'name': details.get('result').get('name'),
            'address': details.get('result').get('formatted_address', ''),
            'phone': details.get('result').get('formatted_phone_number', '')
        })
        return place

    def search(self, company):
        """
        Return a dictonary containt information of a
        suspect place arround a given position.
        A suspect place is some company that match a suspect keyword
        in a Google Places search.

        :param company: (dict) with latitude and longitude keys (as floats)
        :return: closest_suspect_place, a dict with the keys:
            * name : The name of suspect place
            * latitude : The latitude of suspect place
            * longitude : The longitude of suspect place
            * distance : The distance in meters between suspect place and the
              given lat, lng
            * address : The address  of suspect place
            * phone : The phone of suspect place
            * id : The Google Place ID of suspect place
            * keyword : The Keyword that generate the place
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
        lat, lng = float(company['latitude']), float(company['longitude'])
        if math.isnan(lat) or math.isnan(lng):
            return None

        # Get the closest place inside all the searched keywords
        suspicious_places = self.find_places(company, keywords)
        try:
            closest_place = min(suspicious_places, key=lambda x: x['distance'])
        except ValueError:
            return None  # i.e, not suspect place found around

        # skip "hotel" when category is "motel"
        place = self.place_details(closest_place)
        if 'hotel' in place['name'].lower() and keyword == 'Motel':
            return None

        return place


def search_suspicious_around_companies(companies):
    """
    :param companies: pandas dataframe.
    """
    rows = companies.to_dict('records')
    total = len(rows)
    count = 0
    with Pool(processes=4) as pool:
        for company in pool.imap(search_suspicious_around_company, rows):
            count += 1
            print_status(total, count)
            if company:
                write_csv(company)


def search_suspicious_around_company(company):
    """
    :param company: (dict)
    :return: suspect
    """
    latitude, longitude = company.get('latitude'), company.get('longitude')
    if not latitude or not longitude:
        msg = 'No geolocation information for company: {} ({})'
        print(msg.format(company['name'], company['cnpj']))
        return None

    sp = SuspiciousPlaceSearch(settings.get('Google', 'APIKey'))
    return sp.search(company)


def write_csv(company=None):
    if company or not os.path.exists(OUTPUT):
        csv_io = StringIO()
        fieldnames = ('id', 'keyword', 'latitude', 'longitude', 'distance',
                      'name', 'address', 'phone', 'cnpj')

        writer = csv.DictWriter(csv_io, fieldnames=fieldnames)
        if company:
            writer.writerow(company)
        else:
            writer.writeheader()

        with lzma.open(OUTPUT, 'at') as output:
            print(csv_io.getvalue(), file=output)

        csv_io.close()


def get_companies_path():
    return get_path(r'^[\d-]{11}companies.xz$')


def get_suspicious_path():
    return get_path(r'^[\d-]{11}suspicious_distances.xz$')


def get_path(regex):
    for file_name in os.listdir('data'):
        if re.compile(regex).match(file_name):
            return os.path.join('data', file_name)


def print_status(total, count):
    status = '[ {0:.1f}% ]'.format((count * 100) / total)
    return print(status, end='\r')


if __name__ == '__main__':

    # get companies dataset
    companies_path = get_companies_path()
    companies = pd.read_csv(companies_path, low_memory=False)

    # check for existing suspicious places dataset
    suspicious_path = get_suspicious_path()
    if suspicious_path:
        suspicious = pd.read_csv(suspicious_path, low_memory=False)
        if suspicious_path != OUTPUT:
            copyfile(suspicious_path, OUTPUT)
        remaining = companies[~companies.cnpj.isin(suspicious.cnpj)]

    # start a suspicious places dataset if it doesn't exist
    else:
        remaining = companies
        write_csv()

    # run
    print('{} companies'.format(len(companies)))
    print('{} pending'.format(len(remaining)))
    search_suspicious_around_companies(remaining)
