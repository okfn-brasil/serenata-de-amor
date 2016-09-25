from pyquery import PyQuery as pq
import urllib
import sys
import os
from datetime import datetime

"""
SICONV

Reference: https://github.com/datasciencebr/serenata-de-amor/issues/67
"""
os.chdir('..')
URL_BASE = "http://portal.convenios.gov.br"
DATA_PATH = os.getcwd() + '/data/'

def parser_html_page(url):
    return urllib.urlopen(url).read()

def collect_zip_links(page):
    files_links = page('div.item-page p a')
    links = [URL_BASE + a.attrib['href'] if '.zip' in a.attrib['href'] else None for a in files_links]
    return filter(None, links)

def parser_date(page):
    last_extraction_date = page('div.item-page p strong').text()
    #Original: 09/09/2016 04:41:36 Modelo de Dados (v1):
    parsed_date = last_extraction_date[:last_extraction_date.find(" Modelo de Dados (v1):")]
    parsed_date = parsed_date.encode('UTF-16LE').decode('UTF-16')

    date_object = datetime.strptime(parsed_date, '%d/%m/%Y %H:%M:%S')
    return date_object.strftime('%Y-%m-%d')

def save_file(url, last_extraction_date):
    file_name_from_url = url[url.rfind('/')+1:]
    file_name = last_extraction_date + '-' + file_name_from_url.replace('_', '-')
    try:
        urllib.urlretrieve(url, DATA_PATH + file_name)
        return True
    except:
        print 'Error:', url, sys.exc_info()[0]
        return False

def download_files(links, last_extraction_date):
    for link in links:
        print link
        save_file(link, last_extraction_date)

#TODO [WIP] compress the csv's file with .xz

def main():
    url = URL_BASE + "/download-de-dados"
    html_page = pq(parser_html_page(url))

    links = collect_zip_links(html_page)
    last_extraction_date = parser_date(html_page)

    download_files(links, last_extraction_date)

if __name__ == '__main__':
    main()
