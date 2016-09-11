import json
import sys
from csv import DictWriter
from datetime import datetime
from io import StringIO

from bs4 import BeautifulSoup
from lxml.etree import iterparse

XML_FILE_PATH = sys.argv[1]
CSV_FILE_PATH = sys.argv[2]
HTML_FILE_PATH = 'data/datasets-format.html'


def output(*args, **kwargs):
    """Helper to print messages with a date/time marker"""
    now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
    return print(now, *args, **kwargs)


def xml_parser(xml_path, tag='DESPESA'):
    """
    Generator that parses the XML yielding a StringIO object for each record
    found. The StringIO holds the data in JSON format.
    """
    for event, element in iterparse(xml_path, tag=tag):

        # get data
        fields = {c.tag: c.text for c in element.iter() if c.tag != tag}
        element.clear()

        # export in JSON format
        yield StringIO(json.dumps(fields))


def csv_header(html_path):
    """
    Generator that yields the CSV headers reading them from a HTML file (e.g.
    datasets-format.html).
    """
    yield 'ideDocumento'  # this field is missing from the reference
    with open(html_path, 'rb') as file_handler:
        parsed = BeautifulSoup(file_handler.read(), 'lxml')
        for row in parsed.select('.tabela-2 tr'):
            try:
                yield row.select('td')[0].text.strip()
            except IndexError:
                pass


def create_csv(csv_path, headers):
    """Creates the CSV file with the headers (must be a list)"""
    with open(csv_path, 'w') as csv_file:
        writer = DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()


output('Creating the CSV file')
headers = list(csv_header(HTML_FILE_PATH))
create_csv(CSV_FILE_PATH, headers)

output('Reading the XML file')
count = 1
for json_io in xml_parser(XML_FILE_PATH):

    # convert json to csv
    csv_io = StringIO()
    writer = DictWriter(csv_io, fieldnames=headers)
    writer.writerow(json.loads(json_io.getvalue()))

    output('Writing record #{:,} to the CSV'.format(count), end='\r')
    with open(CSV_FILE_PATH, 'a') as csv_file:
        print(csv_io.getvalue(), file=csv_file)
    csv_io.close()

    json_io.close()
    csv_io.close()
    count += 1

print('')  # clean the last output (the one with end='\r')
output('Done!')
