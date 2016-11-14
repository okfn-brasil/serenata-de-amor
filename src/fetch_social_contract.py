import csv
import json
import os
from unicodedata import normalize

import requests
from bs4 import BeautifulSoup


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')


def download(content_names):
    """ this method is responsible for manage and write the dump
    :param content_names: Is a Dictionary list with the deputies
    :return: void
    """
    deputy_companies = []

    deputies = content_names
    size_process = 0
    for deputy in deputies:
        print("[+] GET_INFO[%s][%d]" % (deputy['nomeParlamentar'], size_process))
        deputy_companies.extend(get_info(deputy))
        size_process += 1

    keys = deputies[0].keys()

    print("[+] Writing File...")
    with open(os.path.join(DATA_DIR, 'fetch_deputies.csv'), 'w') as csv_file:

        writer = csv.DictWriter(csv_file, delimiter=';', fieldnames=keys)
        writer.writeheader()
        writer.writerows(deputies)

    print("[+] Done.")


def get_info(deputy):
    """ Scraping information method
        @:param deputy: dictionary of deputy exported from get_content_names()
        @:return List of dictionary with CNPJS and companies of deputies
    """
    list_deputies_companies = []

    name_request = format_for_request(deputy['nomeCompleto'])

    content = get_content_social(name_request)
    soup = BeautifulSoup(content, 'html.parser')
    companies = soup.find_all('div', attrs={'class': 'c-data'})

    for company in companies:
        deputy_company = {}

        line_fantasy = company.find('p', attrs={'class': 'bname'})
        line_cnpj = company.find('p', attrs={'class': 'number'})

        deputy_company['parliamentary_name'] = deputy['nomeParlamentar']
        deputy_company['fullname'] = deputy['nomeCompleto']

        deputy_company['fantasy_name'] = line_fantasy.find('span', attrs={'class': 'text'}).text
        deputy_company['number'] = line_cnpj.find('span', attrs={'class': 'text'}).text

        list_deputies_companies.append(deputy)

    print("[+] COMPANIES_LOADED[%s]" % name_request)

    return list_deputies_companies


def get_content_social(name):
    """ Get html content from consulta socio
        @:param name: name of deputy
        @:return html content with information of social contract
    """
    page = requests.get('http://www.consultasocio.com/q/sa/' + name)
    html = page.content

    return html


def get_content_deputy():
    """ make a request for get a list of deputies
        @:return List dictionary of deputies
     """
    page = requests.get('http://meucongressonacional.com/api/001/deputado')
    data = json.loads(page.content.decode('utf-8'))
    print('[+] GET_NAMES[ LOADED ]')
    return data


def format_for_request(name):
    """ Format name for request in consultasocio.com
    :param name: string
    :return: string formated. Example: WISNER OLIVEIRA, return wisner-oliveira
    """
    cleaned_name = remove_special_characters(name)
    cleaned_name = str.lower(cleaned_name)

    return '-'.join(cleaned_name.split(' '))


def remove_special_characters(name):
    """ Remove special characters
        @:param name: string
    """

    # NFKD is a normal form
    return normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')


download(get_content_deputy())









