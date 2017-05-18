import asyncio
import json
import logging
import math
import os
import sys
from argparse import ArgumentParser
from concurrent.futures import CancelledError
from configparser import RawConfigParser
from csv import DictWriter
from datetime import date
from io import StringIO
from itertools import chain
from pathlib import Path
from urllib.parse import urlencode

import aiofiles
import aiohttp
import pandas as pd
import numpy as np
from geopy.distance import vincenty


DTYPE = dict(cnpj=np.str, cnpj_cpf=np.str)
LOG_FORMAT = '[%(levelname)s] %(asctime)s: %(message)s'

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=LOG_FORMAT)


class GooglePlacesURL:

    BASE_URL = 'https://maps.googleapis.com/maps/api/place/'

    def __init__(self, key):
        self.key = key

    def url(self, endpoint, query=None, format='json'):
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

    def details(self, place):
        """
        :param place: (int or str) ID of the place in Google Place
        :return: (str) URL to do a place details Google Places search
        """
        query = (('placeid', place),)
        return self.url('details', query)

    def nearby(self, keyword, location):
        """
        :param keywork: (str) category to search places
        :return: (str) URL to do a nearby Google Places search
        """
        query = (
            ('location', location),
            ('keyword', keyword),
            ('rankby', 'distance'),
        )
        return self.url('nearbysearch', query)


class SexPlacesNearBy:

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
        self.url = GooglePlacesURL(key or settings.get('Google', 'APIKey'))

        self.company = company
        self.latitude = self.company['latitude']
        self.longitude = self.company['longitude']
        self.places = []
        self.closest = None

    @property
    def company_name(self):
        return self.company.get('trade_name') or self.company.get('name')

    @property
    def valid(self):
        try:
            coords = map(float, (self.latitude, self.longitude))
        except ValueError:
            return False

        if any(map(math.isnan, coords)):
            return False

        return True

    async def get_closest(self):
        """
        Start the requests to store a place per self.KEYWORD in self.places.
        Then gets the closest place found, queries for its details and returns
        a dict with the details for that place.
        """
        if not self.valid:
            msg = 'No geolocation information for company: {} ({})'
            logging.info(msg.format(self.company_name, self.company['cnpj']))
            return None

        tasks = [self.load_place(k) for k in self.KEYWORDS]
        await asyncio.gather(*tasks)
        ordered = sorted(self.places, key=lambda x: x['distance'])

        for place in ordered:
            place = await self.load_details(place)
            name = place.get('name', '').lower()

            if place.get('keyword') == 'motel' and 'hotel' in name:
                pass  # google returns hotels when looking for a motel

            else:
                prefix = '💋 ' if place.get('distance') < 5 else ''
                msg = '{}Found something interesting {:.2f}m away from {}…'
                args = (prefix, place.get('distance'), self.company_name)
                logging.info(msg.format(*args))
                self.closest = place
                return place

    async def load_place(self, keyword, print_status=False):
        """
        Given a keyword it loads the place returned by the API to self.places.
        """
        if print_status:
            msg = 'Looking for a {} near {} ({})…'
            args = (keyword, self.company_name, self.company.get('cnpj'))
            logging.info(msg.format(*args))


        location = '{},{}'.format(self.latitude, self.longitude)
        url = self.url.nearby(keyword, location)
        try:
            response = await aiohttp.request('GET', url)
        except aiohttp.TimeoutError:
            logging.info('Timeout raised for {}'.format(url))
        else:
            content = await response.text()
            place = self.parse(keyword, content)
            if place and isinstance(place.get('distance'), float):
                self.places.append(place)

    def parse(self, keyword, content):
        """
        Return a dictionary with information of the nearest sex place
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

        Google responses:
            * `OK` indicates that no errors occurred; the place was
              successfully detected and at least one result was returned.
            * `UNKNOWN_ERROR` indicates a server-side error; trying again may
              be successful.
            * `ZERO_RESULTS` indicates that the reference was valid but no
              longer refers to a valid result. This may occur if the
              establishment is no longer in business.
            * `OVER_QUERY_LIMIT` indicates that you are over your quota.
            * `REQUEST_DENIED` indicates that your request was denied,
              generally because of lack of an invalid key parameter.
            * `INVALID_REQUEST` generally indicates that the query (reference)
              is missing.
            * `NOT_FOUND` indicates that the referenced location was not found
              in the Places database.<Paste>

        Source: https://developers.googlefetchplaces/web-service/details
        """
        response = json.loads(content)
        status = response.get('status')

        if status != 'OK':
            if status in ('OVER_QUERY_LIMIT', 'REQUEST_DENIED'):
                shutdown()  # reached API limit or API key is missing/wrong

            if status != 'ZERO_RESULTS':
                error = response.get('error', '')
                msg = 'Google Places API Status: {} {}'.format(status, error)
                logging.info(msg.strip())

            return None

        place, *_ = response.get('results', [{}])

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
            'cnpj': self.company.get('cnpj'),
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

        # request place details
        try:
            response = await aiohttp.request('GET', self.url.details(place_id))
        except aiohttp.TimeoutError:
            logging.info('Timeout raised for {}'.format(url))
            return place
        else:
            content = await response.text()

        # parse place details
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


async def fetch_place(company, output, semaphore):
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
    logging.info("Let's get started!")

    # write CSV data
    for company_row in companies.itertuples(index=True):
        company = dict(company_row._asdict())  # _asdict() returns OrderedDict
        tasks.append(fetch_place(company, output, semaphore))

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

    logging.info('Loading {}'.format(filepath))
    dataset = pd.read_csv(
        filepath,
        dtype=DTYPE,
        low_memory=False,
        usecols=usecols
    )
    dataset = dataset.fillna(value=na_value)
    return dataset


def get_companies(companies_path, **kwargs):
    """
    Compares YYYY-MM-DD-companies.xz with the newest
    YYYY-MM-DD-sex-place-distances.xz and returns a DataFrame with only
    the rows matching the search criteria, excluding already fetched companies.

    Keyword arguments are expected: term (int), value (float) and city (str)
    """
    filters = tuple(map(kwargs.get, ('term', 'value', 'city')))
    if not all(filters):
        raise TypeError('get_companies expects term, value and city as kwargs')
    term, value, city = filters

    # load companies
    cols = ('cnpj', 'trade_name', 'name', 'latitude', 'longitude', 'city')
    companies = load_newest_dataset(companies_path, cols)
    companies['cnpj'] = companies['cnpj'].str.replace(r'\D', '')

    # load & fiter reimbursements
    cols = ('total_net_value', 'cnpj_cpf', 'term')
    reimbursements = load_newest_dataset('data/*-reimbursements.xz', cols)
    query = '(term == {}) & (total_net_value >= {})'.format(term, value)
    reimbursements = reimbursements.query(query)

    # load & filter companies
    on = dict(left_on='cnpj', right_on='cnpj_cpf')
    companies = pd.merge(companies, reimbursements, **on)
    del(reimbursements)
    companies.drop_duplicates('cnpj', inplace=True)
    query = 'city.str.upper() == "{}"'.format(city.upper())
    companies = companies.query(query)

    # clean up companies
    del(companies['cnpj_cpf'])
    del(companies['term'])
    del(companies['total_net_value'])
    del(companies['city'])

    # load sexplaces & filter remaining companies
    cols = ('cnpj', )
    sex_places = load_newest_dataset('data/*-sex-place-distances.xz', cols)
    if sex_places is None or sex_places.empty:
        return companies

    return companies[~companies.cnpj.isin(sex_places.cnpj)]


def is_new_dataset(output):
    sex_places = find_newest_file('*sex-place-distances.xz', 'data')
    if not sex_places:
        return True

    # convert previous database from xz to csv
    pd.read_csv(sex_places, dtype=DTYPE).to_csv(output, index=False)
    os.remove(sex_places)
    return False


def convert_to_lzma(csv_output, xz_output):
    uncompressed = pd.read_csv(csv_output, dtype=DTYPE)
    uncompressed.to_csv(xz_output, compression='xz', index=False)
    os.remove(csv_output)


def shutdown():
    """
    Something is wrong and it does not worth it to keep running. This method
    cancels all pending coroutines so the script can wrap up data collection
    and move on (that is to say, compress the output we've got so far as an
    .xz file).
    """
    for task in asyncio.Task.all_tasks():
        task.cancel()


def main(companies_path, max_requests=500, sample_size=None, filters=None):
    if not filters:
        filters = dict()

    if not os.path.exists(companies_path):
        logging.info('File not found: {}'.format(companies_path))
        return

    # set file paths
    directory = os.path.dirname(os.path.abspath(companies_path))
    name = '{}-sex-place-distances.{}'
    today = date.today().strftime('%Y-%m-%d')
    csv_output = os.path.join(directory, name.format(today, 'csv'))
    xz_output = os.path.join(directory, name.format(today, 'xz'))

    # get companies
    companies = get_companies(companies_path, **filters)
    if sample_size:
        companies = companies.sample(sample_size)

    # check we have data to work on
    if companies.empty:
        logging.info('Nothing to fetch.')
        return None

    # run
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main_coro(companies, csv_output, max_requests))
    except CancelledError:
        logging.debug('All async tasks were stopped')
    finally:
        convert_to_lzma(csv_output, xz_output)


if __name__ == '__main__':
    description = (
        'Fetch the closest sex place to each company. '
        'Requires a Google Places API key set at config.ini.'
    )
    parser = ArgumentParser(description=description)
    parser.add_argument('companies_path', help='Companies .xz datset')
    parser.add_argument(
        '--max-parallel-requests', '-r', type=int, default=500,
        help='Max parallel requests (default: 500)'
    )
    parser.add_argument(
        '--sample-size', '-s', type=int, default=None,
        help='Limit fetching to a given sample size (default: None)'
    )
    parser.add_argument(
        '--city', '-c', required=True,
        help='Limit fetching to a given city (required)'
    )
    parser.add_argument(
        '--min-value', '-m', type=float, required=True,
        help='Limit fetching to expensed higher to a minimum amount (required)'
    )
    parser.add_argument(
        '--term', '-t', type=int, required=True,
        help='Limit fetching to a given term (required)'
    )
    args = parser.parse_args()

    # max parallel requests must be at least 13 (requests needed per company)
    if args.max_parallel_requests < 13:
        args.max_parallel_requests = 13

    main(
        args.companies_path,
        args.max_parallel_requests,
        args.sample_size,
        dict(term=args.term, city=args.city, value=args.min_value)
    )
