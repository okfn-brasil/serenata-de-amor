import csv
import gc
import json
import os
import sys
from datetime import datetime
from tempfile import TemporaryDirectory

import numpy as np
from bs4 import BeautifulSoup

XML_FILE_PATH = sys.argv[1]
CSV_FILE_PATH = sys.argv[2]

field_names = ['ideDocumento']
tmp_files = []


def output(msg, **kwargs):
    now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
    return print(now, msg, **kwargs)

# get extra field names
output('Fetching CSV headers')
with open('data/datasets_format.html', 'rb') as file_handler:
    parsed = BeautifulSoup(file_handler.read(), 'lxml')
    for row in parsed.select('.tabela-2 tr'):
        try:
            field_names.append(row.select('td')[0].text.strip())
        except IndexError:
            pass
    del(parsed)
    gc.collect()

# read and parse XML source
output('Reading XML file')
xml_data = np.fromfile(XML_FILE_PATH, dtype=np.uint8, count=-1)
output('Parsing XML contents (this might take several minutes)')
xml_soup = BeautifulSoup(xml_data.tobytes(), 'lxml-xml')
records = xml_soup.find_all('DESPESA')

with TemporaryDirectory() as tmp_dir:

    # create tmp files with data (avoid requiring large amounts of RAM)
    output('Saving XML data to a temporary directory')
    for index, record in enumerate(records):

        # print status
        total = len(records)
        count = index + 1
        status = 'Saving record {:,} of {:,}'.format(count, total)
        output(status, end='\r')

        # save contents to a tmp file and add file to the list of tmp files
        attributes = {attr.name: attr.string for attr in record.contents}
        tmp_path = os.path.join(tmp_dir, str(index) + '.json')
        with open(tmp_path, 'w') as file_handler:
            file_handler.write(json.dumps(attributes))
        tmp_files.append(tmp_path)

        if count == total:
            output('Cleaning up (this might take several minutes)')

    # free some memory
    del(records)
    del(xml_soup)
    gc.collect()

    # write contents to CSV
    output('Writing data to CSV file')
    with open(CSV_FILE_PATH, 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        for index, tmp_path in enumerate(tmp_files):

            # print status
            total = len(tmp_files)
            count = index + 1
            status = 'Writing record {:,} of {:,}'.format(count, total)
            output(status, end='\r')

            # write to CSV (and delete temp file)
            with open(tmp_path, 'r') as file_handler:
                writer.writerow(json.loads(file_handler.read()))

            if count == total:
                output('Cleaning up (this might take several minutes)')

output('Done!')
