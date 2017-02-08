import datetime
import warnings
import requests

STARTING_YEAR = 2011
NOW = datetime.datetime.now()
SERVER = 'http://arquivos.portaldatransparencia.gov.br/'
PATH = 'downloads.asp?a={}&m={:02d}&consulta=BolsaFamiliaFolhaPagamento'


def urls():
    for year in range(STARTING_YEAR, NOW.year + 1):
        for month in range(1, 13):
            if datetime.datetime(year, month, NOW.day) <= NOW:
                url = SERVER + PATH.format(year, month)
                req = requests.head(url)

                # looks like some devs are not familiar with 404 status
                if req.headers.get('Content-Type') == 'application/x-download':
                    yield url

                else:
                    msg = 'Data from {:02d}/{} could not be located at: {}'
                    warnings.warn(msg.format(month, year, url))


if __name__ == '__main__':
    for url in urls():
        print(url)