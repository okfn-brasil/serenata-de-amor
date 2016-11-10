import configparser
import csv
import datetime
import lzma
import math
import os
import re
from io import StringIO
from multiprocessing import Process, Queue
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
            msg = '\nLooking for a suspicious {} close to {} ({})…'
            print(msg.format(keyword, company['name'], company['cnpj']))

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
                    location = deep_get(place, ['geometry', 'location'])
                    latitude = float(location.get('lat'))
                    longitude = float(location.get('lng'))
                    distance = vincenty((lat, lng), (latitude, longitude))
                    cnpj = ''.join(re.findall(r'[/d]', company['cnpj']))
                    yield {
                        'id': place.get('place_id'),
                        'keyword': keyword,
                        'latitude': latitude,
                        'longitude': longitude,
                        'distance': distance.meters,
                        'cnpj': cnpj
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
            'name': deep_get(details, ['result', 'name']),
            'address': deep_get(details, ['result', 'formatted_address'], ''),
            'phone': deep_get(details, ['result', 'formatted_phone_number'], '')
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
        suspicious_places = list(self.find_places(company, keywords))
        try:
            closest_place = min(suspicious_places, key=lambda x: x['distance'])
        except ValueError:
            return None  # i.e, not suspect place found around

        # skip "hotel" when category is "motel"
        place = self.place_details(closest_place)
        name = place['name']
        if name:
            if 'hotel' in name.lower() and place['keyword'] == 'Motel':
                return None

        return place


def search_suspicious_around_companies(companies):
    """
    :param companies: pandas dataframe.
    """

    def make_queue(q, companies):
        for company in companies.itertuples(index=False):
            company = dict(company._asdict())  # _asdict() gives OrderedDict
            q.put(csv_line(search_suspicious_around_company(company)))

    write_queue = Queue()
    place_search = Process(target=make_queue, args=(write_queue, companies))
    place_search.start()

    with lzma.open(OUTPUT, 'at') as output:
        while place_search.is_alive() or not write_queue.empty():
            try:
                contents = write_queue.get(timeout=1)
                if contents:
                    print(contents, file=output)
            except:
                pass

    place_search.join()


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


def csv_line(company=None, **kwargs):
    if company or not os.path.exists(OUTPUT):
        csv_io = StringIO()
        fieldnames = ('id', 'keyword', 'latitude', 'longitude', 'distance',
                      'name', 'address', 'phone', 'cnpj')

        writer = csv.DictWriter(csv_io, fieldnames=fieldnames)
        if company:
            contents = {k: v for k, v in company.items() if k in fieldnames}
            writer.writerow(contents)
        elif kwargs.get('headers'):
            writer.writeheader()

        contents = csv_io.getvalue()
        csv_io.close()
        return contents


def get_companies_path():
    return get_path(r'^[\d-]{11}companies.xz$')


def get_suspicious_path():
    return get_path(r'^[\d-]{11}suspicious_distances.xz$')


def get_path(regex):
    for file_name in os.listdir('data'):
        if re.compile(regex).match(file_name):
            return os.path.join('data', file_name)


def deep_get(dictionary, keys, default=None):
    """
    :param: (dict) usually a nested dict
    :param: (list) keys as strings
    :return: value or None

    Example:
    >>> d = {'ahoy': {'capn': 42}}
    >>> deep_get(['ahoy', 'capn'], d)
    42
    """
    if not keys:
        return None

    if len(keys) == 1:
        return dictionary.get(keys[0], default)

    return deep_get(dictionary.get(keys[0], {}), keys[1:])


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
        try:
            remaining = companies[~companies.cnpj.isin(suspicious.cnpj)]
        except AttributeError:  # if file exists but is empty
            remaining = companies

    # start a suspicious places dataset if it doesn't exist
    else:
        remaining = companies
        with lzma.open(OUTPUT, 'at') as output:
            print(csv_line(headers=True), file=output)

    # run
    print('{} companies'.format(len(companies)))
    print('{} pending'.format(len(remaining)))
    search_suspicious_around_companies(remaining)
