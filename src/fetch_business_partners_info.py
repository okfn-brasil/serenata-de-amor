import os
import json
import datetime
import time
import re
import pandas as pd
from unicodedata import normalize
from selenium import webdriver
from bs4 import BeautifulSoup
import platform
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))


def selenium_webdriver():
    webdrivers = {
        'linux_32bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_linux32.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver.exe',
                'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-linux32.tar.gz',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver', 'object': webdriver.Firefox
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_linux32.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver', 'object': webdriver.Opera
            }
        ],
        'linux_64bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_linux64.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver', 'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_linux64.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver', 'object': webdriver.Opera
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-linux64.tar.gz',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver', 'object': webdriver.Firefox
            }
        ],
        'Darwin_64bit': [
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_mac64.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver', 'object': webdriver.Opera
            },
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_mac64.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver', 'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-macos.tar.gz',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver', 'object': webdriver.Firefox
            }
        ],
        'Windows_32bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_win32.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver.exe',
                'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-win32.zip',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver.exe', 'object': webdriver.Firefox
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_win32.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver.exe', 'object': webdriver.Opera
            }
        ],
        'Windows_64bit': [
            {
                'url': 'https://chromedriver.storage.googleapis.com/2.27/chromedriver_win32.zip',
                'capabilities': DesiredCapabilities.CHROME, 'file_name': 'chromedriver.exe', 'object': webdriver.Chrome
            },
            {
                'url': 'https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-win64.zip',
                'capabilities': DesiredCapabilities.FIREFOX, 'file_name': 'geckodriver.exe', 'object': webdriver.Firefox
            },
            {
                'url': 'https://github.com/operasoftware/operachromiumdriver/releases/download/v0.2.2/operadriver_win64.zip',
                'capabilities': DesiredCapabilities.OPERA, 'file_name': 'operadriver.exe', 'object': webdriver.Opera
            }
        ]
    }

    platform_name = '%s_%s' % (platform.system(), platform.architecture()[0])
    assert platform_name in webdrivers, 'Your platform is not compatible with Selenium WebDrivers supported'
    driver_list = webdrivers[platform_name]

    for driver_info in driver_list:
        try:
            executable_path = os.path.abspath(driver_info['file_name'])
            # TODO: Verificar se o arquivo existe, caso nao exista baixar o mesmo e descompactar se necessario colocando
            # no path local e no diretorio de destino (diretorio local)
            return driver_info['object'](executable_path=executable_path,
                                         desired_capabilities=driver_info['capabilities'])
        except WebDriverException:
            pass


def find_newest_file(data_dir, name):
    date_regex = re.compile('\d{4}-\d{2}-\d{2}')

    matches = (date_regex.findall(f) for f in os.listdir(data_dir))
    dates = sorted(set([l[0] for l in matches if l]), reverse=True)

    for date in dates:
        filename = '{}-{}'.format(date, name)
        filepath = os.path.join(data_dir, filename)

        if os.path.isfile(filepath):
            return os.path.abspath(filepath)


def normalize_name(name):
    return normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()


def make_google_cache_url(name):
    return 'http://webcache.googleusercontent.com/search?btnG=Search&q=cache:%s' % make_consulta_socio_url(name)


def make_consulta_socio_url(name):
    return 'http://www.consultasocio.com/q/sa/%s' % normalize_name(name).replace(' ', '-')


def extract_info_from_page(url, driver, error_page_expected_title, origin):
    # Open the page using Selenium in order to collect the full HTML to be parsed by BeautifulSoup
    driver.get(url)
    driver.switch_to.default_content()
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Somethimes google can ask for captcha, so you should type it!
    if 'To continue, please type the characters below:' in soup.text:
        while 'To continue, please type the characters below:' in soup.text:
            driver.switch_to.default_content()
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            time.sleep(1)

    # Collect the information if there is no error
    if error_page_expected_title.lower() not in soup.title.text.lower():
        info = {'partners': [], 'business': []}

        for partner in soup.findAll('span', attrs={'class': 'socio'}):
            info['partners'].append(partner.text)
        for company_info in soup.findAll('p', attrs={'class': 'number'}):
            info['business'].append(company_info.find('span', {'class': 'text'}).text)

        # Store information about where it's was collected and when just for further analysis and data integrity checks
        info['data_origin'] = origin
        info['collect_date'] = str(datetime.datetime.now())
        return info


def fetch_business_infos():
    output_file_path = find_newest_file(DATA_DIR, 'congressperson-business-partners.json')
    # If there is no previous file to load, let's create a new one.
    if output_file_path is None:
        file_base_name = '{}-congressperson-business-partners.json'.format(datetime.date.today().strftime('%Y-%m-%d'))
        output_file_path = os.path.join(DATA_DIR, file_base_name)

    # Load cached data if file exists
    result = {}
    if os.path.exists(output_file_path):
        result = json.loads(open(output_file_path, 'r').read())

    # Collect the information from all congress person
    civil_names_df = pd.read_csv(find_newest_file(DATA_DIR, 'congressperson-civil-names.xz'))

    driver = selenium_webdriver()

    original_site_blocked = False
    id = 0
    collected_count = 0
    total_count = len(civil_names_df['civil_name'].unique())
    info = None
    for name in civil_names_df['civil_name'].unique():
        name = normalize_name(name).upper()

        print('(%d/%d) %s' % (id, total_count, name), sep=' ', end='\r')
        if name in result:
            collected_count += 1
        else:
            if not original_site_blocked:
                info = extract_info_from_page(make_consulta_socio_url(name), driver, 'Uso — ConsultaSocio.com',
                                              'ConsultaSocio')
                original_site_blocked = info is None
            if original_site_blocked:
                info = extract_info_from_page(make_google_cache_url(name), driver, 'error', 'GoogleCache')
            if info:
                result[name] = info
                open(output_file_path, 'w').write(json.dumps(result))
                collected_count += 1
        id += 1
    driver.quit()
    print('%d informations collected from %d' % (collected_count, total_count))
    return result


if __name__ == '__main__':
    print("""
    Uses Google Cache information about http://www.consultasocio.com in order to collect all the business partners from company or person name
    """)
    print('Started at', str(datetime.datetime.now()))
    fetch_business_infos()
    print('Finished at', str(datetime.datetime.now()))

# TODO: Gerar um arquivo csv no final com as informacoes (e nao um json)
