import asyncio
import json
import math
import os
import re
from argparse import ArgumentParser
from csv import DictWriter
from configparser import RawConfigParser
from datetime import date
from io import StringIO
from itertools import chain
from pathlib import Path
from urllib.parse import urlencode

import aiofiles
import pandas as pd
from aiohttp import request
from geopy.distance import vincenty


class SexPlacesNearBy:

    BASE_URL = 'https://maps.googleapis.com/maps/api/place/'
    KEYWORDS = ('acompanhantes',
                'adult entertainment club',
                'adult entertainment store',
                'gay sauna',
                'massagem',
                'modeling agency',
                'motel',
                'night club',
                'sex club',
                'sex shop',
                'strip club',
                'swinger clubs')

    def __init__(self, company, key=None):
        """
        :param company: (dict) Company with name, cnpj, latitude and longitude
        :param key: (str) Google Places API key
        """
        settings = RawConfigParser()
        settings.read('config.ini')
        self.company = company
        self.key = key or settings.get('Google', 'APIKey')
        self.latitude = self.company['latitude']
        self.longitude = self.company['longitude']
        self.places = []
        self.closest = None

    @property
    def company_name(self):
        return self.company.get('trade_name') or self.company.get('name')

    async def get_all_places(self):
        """
        Use aiohttp to get the closest place to the company according to each
        keyworn. Returns `None`, the results are saved on self.places.
        """
        tasks = [self.load_place(k) for k in self.KEYWORDS]
        await asyncio.gather(*tasks)

    async def get_closest(self):
        """
        Gets the closest place find in reads self.places, queries for its
        details and returns a dict with all the info on that place.
        """
        if not self.is_valid():
            return None

        await self.get_all_places()
        ordered = sorted(self.places, key=lambda x: x['distance'])

        for place in ordered:
            place = await self.load_details(place)
            name = place.get('name', '').lower()

            if place['keyword'] == 'motel' and 'hotel' in name:
                pass  # google returns hotels when looking for a motel

            else:
                prefix = '💋 ' if place['distance'] < 5 else ''
                msg = '{}Found something interesting {:.2f}m away from {}…'
                args = (prefix, place.get('distance'), self.company_name)
                print(msg.format(*args))
                self.closest = place
                return place

    @staticmethod
    def is_valid_coordinate(coord):
        try:
            as_float = float(coord)
        except ValueError:
            return False

        return False if math.isnan(as_float) else True

    def is_valid(self):
        coords = (self.latitude, self.longitude)
        if not all(map(self.is_valid_coordinate, coords)):
            msg = 'No geolocation information for company: {} ({})'
            print(msg.format(self.company_name, self.company['cnpj']))
            return False

        return True

    async def load_place(self, keyword):
        """
        Given a keyword it loads the place returned by the API to self.places.
        """
        keyword, content = await self.get(keyword)
        place = self.parse(keyword, content)
        if place and isinstance(place.get('distance'), float):
            self.places.append(place)

    async def get(self, keyword, print_status=False):
        if print_status:
            msg = 'Looking for a {} near {} ({})…'
            args = (keyword, self.company_name, self.company.get('cnpj'))
            print(msg.format(*args))

        url = self.nearby_url(keyword)
        response = await request('GET', url)
        content = await response.text()
        return keyword, content

    def parse(self, keyword, content):
        """
        Return a dictonary with information of the nearest sex place
        around a given company.
        :param keyword: (str) keyword used by the request
        :param content: (str) content of the response to the request
        :return: (dict) with
            * name : The name of nearest sex place
            * latitude : The latitude of nearest sex place
            * longitude : The longitude of nearest sex place
            * distance : Distance (in meters) between the company and the
              nearest sex place
            * address : The address of the nearest sex place
            * phone : The phone of the nearest sex place
            * id : The Google Place ID of the nearest sex place
            * keyword : term that matched the sex place in Google Place Search
        """
        response = json.loads(content)
        if response['status'] != 'OK':
            if 'error_message' in response:
                status, error = response.get('status'), response.get('error')
                print('{}: {}'.format(status, error))
            elif response.get('status') != 'ZERO_RESULTS':
                msg = 'Google Places API Status: {}'
                print(msg.format(response.get('status')))

        else:
            place = response.get('results', [{}])[0]

            location = place.get('geometry', {}).get('location', {})
            latitude = float(location.get('lat'))
            longitude = float(location.get('lng'))

            company_location = (self.latitude, self.longitude)
            place_location = (latitude, longitude)
            distance = vincenty(company_location, place_location)

            return {
                'id': place.get('place_id'),
                'keyword': keyword,
                'latitude': latitude,
                'longitude': longitude,
                'distance': distance.meters,
                'cnpj': re.sub(r'\D', '', self.company.get('cnpj')),
                'company_name': self.company.get('name'),
                'company_trade_name': self.company.get('trade_name')
            }

    async def load_details(self, place):
        """
        :param place: dictionary with id key.
        :return: dictionary updated with name, address and phone.
        """
        place_id = place.get('id')
        if not place_id:
            return place

        response = await request('GET', self.details_url(place_id))
        content = await response.text()

        try:
            details = json.loads(content)
        except ValueError:
            return place
        else:
            if not details:
                return place

        result = details.get('result', {})
        place.update(dict(
            name=result.get('name', ''),
            address=result.get('formatted_address', ''),
            phone=result.get('formatted_phone_number', '')
        ))
        return place

    def details_url(self, place):
        """
        :param place: (int or str) ID of the place in Google Place
        :return: (str) URL to do a place details Google Places search
        """
        query = (('placeid', place),)
        return self.google_places_url('details', query)

    def nearby_url(self, keyword):
        """
        :param keywork: (str) category to search places
        :return: (str) URL to do a nearby Google Places search
        """
        location = '{},{}'.format(self.latitude, self.longitude)
        query = (
            ('location', location),
            ('keyword', keyword),
            ('rankby', 'distance'),
        )
        return self.google_places_url('nearbysearch', query)

    def google_places_url(self, endpoint, query=None, format='json'):
        """
        :param endpoint: (str) Google Places API endpoint name (e.g. details)
        :param query: (tuple) tuples with key/values pairs for the URL query
        :param format: (str) output format (default is `json`)
        :return: (str) URL to do an authenticated Google Places request
        """
        key = ('key', self.key)
        query = tuple(chain(query, (key,))) if query else (key)
        parts = (
            self.BASE_URL,
            endpoint,
            '/{}?'.format(format),
            urlencode(query)
        )
        return ''.join(parts)


async def write_to_csv(path, place=None, **kwargs):
    """
    Receives a given place (dict) and writes it in the CSV format into path.
    CSV headers are defined in `fields`. The named argument `headers`
    (bool) determines if the functions write the CSV header or not.
    """
    headers = kwargs.get('headers', False)
    if not place and not headers:
        return

    fields = (
        'id', 'keyword', 'latitude', 'longitude', 'distance', 'name',
        'address', 'phone', 'cnpj', 'company_name', 'company_trade_name'
    )

    with StringIO() as obj:
        writer = DictWriter(obj, fieldnames=fields, extrasaction='ignore')
        if headers:
            writer.writeheader()
        if place:
            writer.writerow(place)

        async with aiofiles.open(path, mode='a') as fh:
            await fh.write(obj.getvalue())


async def write_place(company, output, semaphore):
    """
    Gets a company (dict), finds the closest place nearby and write the result
    to a CSV file.
    """
    with (await semaphore):
        places = SexPlacesNearBy(company)
        await places.get_closest()
        if places.closest:
            await write_to_csv(output, places.closest)


async def main_coro(companies, output, max_requests):
    """
    :param companies: (Pandas DataFrame)
    :param output: (str) Path to the CSV output
    :param max_requests: (int) max parallel requests
    """
    # write CSV headers
    if is_new_dataset(output) and not companies.empty:
        await write_to_csv(output, headers=True)

    semaphore = asyncio.Semaphore(max_requests // 13)  # 13 reqs per company
    tasks = []
    print("Let's get started!")

    # write CSV data
    for company_row in companies.itertuples(index=True):
        company = dict(company_row._asdict())  # _asdict() returns OrderedDict
        tasks.append(write_place(company, output, semaphore))

    await asyncio.wait(tasks)


def find_newest_file(pattern='*.*', source_dir='.'):
    """
    Assuming that the files will be in the form of:
    yyyy-mm-dd-type-of-file.xz we can try to find the newest file
    based on the date.
    """
    files = sorted(Path(source_dir).glob(pattern))
    if not files:
        return None

    file = files.pop()
    if not file:
        return None

    return str(file)


def load_newest_dataset(pattern, usecols, na_value=''):
    filepath = find_newest_file(pattern)
    if not filepath:
        return None

    print('Loading {}'.format(filepath))
    dataset = pd.read_csv(filepath, usecols=usecols, low_memory=False)
    dataset = dataset.fillna(value=na_value)
    return dataset


def get_remaining_companies(companies_path):
    """
    Compares YYYY-MM-DD-companies.xz with the newest
    YYYY-MM-DD-sex-place-distances.xz and returns a DataFrame with only
    unfetched companies.
    """
    cols = ('cnpj', 'trade_name', 'name', 'latitude', 'longitude')
    companies = load_newest_dataset(companies_path, cols)
    sex_places = load_newest_dataset('**/*sex-place-distances.xz', ('cnpj',))

    if sex_places is None or sex_places.empty:
        return companies

    return companies[~companies.cnpj.isin(sex_places.cnpj)]


def is_new_dataset(output):
    sex_places = find_newest_file('*sex-place-distances.xz', 'data')
    if not sex_places:
        return True

    # convert previous database from xz to csv
    pd.read_csv(sex_places).to_csv(output)
    os.remove(sex_places)
    return False


def convert_to_lzma(csv_output, xz_output):
    pd.read_csv(csv_output).to_csv(xz_output, compression='xz')
    os.remove(csv_output)


def main(companies_path, max_requests=500, sample_size=None):

    if not os.path.exists(companies_path):
        print('File not found: {}'.format(companies_path))
        return

    # set file paths
    directory = os.path.dirname(os.path.abspath(companies_path))
    name = '{}-sex-place-distances.{}'
    today = date.today().strftime('%Y-%m-%d')
    csv_output = os.path.join(directory, name.format(today, 'csv'))
    xz_output = os.path.join(directory, name.format(today, 'xz'))

    # get companies
    companies = get_remaining_companies(companies_path)
    if sample_size:
        companies = companies.sample(sample_size)

    # run
    if companies.empty:
        print('Nothing to fetch.')
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_coro(companies, csv_output, max_requests))
        loop.close()
        convert_to_lzma(csv_output, xz_output)


if __name__ == '__main__':
    description = (
        'Fetch the closest sex place to each company. '
        'Requires a Google Places API key set at config.ini.'
    )
    parser = ArgumentParser(description=description)
    parser.add_argument('companies_path', help='Companies .xz datset')
    parser.add_argument(
        '--max-parallel-requests', '-m', type=int, default=500,
        help='Max parallel requests (default: 500)'
    )
    parser.add_argument(
        '--sample-size', '-s', type=int, default=None,
        help='Limit fetching to a given sample size (default: None)'
    )

    args = parser.parse_args()
    main(args.companies_path, args.max_parallel_requests, args.sample_size)
