import configparser
from argparse import ArgumentParser
import os.path
import subprocess
from urllib.request import urlretrieve


def download_source():
    dataset_urls = [
        'http://www.camara.gov.br/cotas/AnoAtual.zip',
        'http://www.camara.gov.br/cotas/AnoAnterior.zip',
        'http://www.camara.gov.br/cotas/AnosAnteriores.zip']
    filenames = map(lambda url: url.split('/')[-1], dataset_urls)

    for url, filename in zip(dataset_urls, filenames):
        filepath = 'data/%s' % filename
        urlretrieve(url, filepath)
        subprocess.call(['unzip', '-o', filepath, '-d', 'data'])

    urlretrieve('http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/explicacoes-sobre-o-formato-dos-arquivos-xml',
                'data/datasets-format.html')


def download_backup():
    settings = configparser.RawConfigParser()
    settings.read('config.ini')
    bucket = settings.get('Amazon', 'Bucket')
    region = settings.get('Amazon', 'Region')

    files = ['2016-08-08-current-year.xz',
             '2016-08-08-last-year.xz',
             '2016-08-08-previous-years.xz',
             '2016-08-08-ceap-datasets.md',
             '2016-08-08-datasets-format.html',
             '2016-09-03-companies.xz']
    for filename in files:
        url = 'https://%s.amazonaws.com/%s/%s' % (region, bucket, filename)
        filepath = 'data/%s' % filename
        if not os.path.exists('data/%s' % filename):
            print('Downloading %s' % filename)
            urlretrieve(url, filepath)

parser = ArgumentParser()
parser.add_argument("-sr", "--from_source",
                    action="store_true",
                    help="download files as provided by original sources")
parser.add_argument("-am", "--from_amazon",
                    action="store_true",
                    help="download files from Amazon backup")
args = parser.parse_args()
if args.from_source :
    download_source()
elif args.from_amazon :
    download_backup()
else:
    print("You need to choose one option: (-sr) or (-am). Use --help to see more details.")
