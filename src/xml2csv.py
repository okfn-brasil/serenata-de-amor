from bs4 import BeautifulSoup
import csv
import sys

XML_FILE_PATH = sys.argv[1]
CSV_FILE_PATH = sys.argv[2]

xml_file = open(XML_FILE_PATH, 'rb').read()
xml_soup = BeautifulSoup(xml_file, 'lxml-xml')

variables_file = open('data/datasets_format.html', 'rb').read()
variables_soup = BeautifulSoup(variables_file, 'lxml')
variables = variables_soup.select('.tabela-2 td')
fieldnames = ['ideDocumento'] + \
    [var.text.strip() for index, var in enumerate(variables) if index % 3 == 0]

with open(CSV_FILE_PATH, 'w') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    records = xml_soup.find_all('DESPESA')
    for record in records:
        record_attributes = \
            dict([(attr.name, attr.string) for attr in record.contents])
        writer.writerow(record_attributes)
