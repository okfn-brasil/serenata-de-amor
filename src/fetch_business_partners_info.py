import os
import json
import datetime
import time
import pandas as pd
from unicodedata import normalize
from selenium import webdriver
from bs4 import BeautifulSoup


def selenium_driver_path():
    for path in ['chromedriver.exe', 'chromedriver']:
        if os.path.exists(path):
            return path
    raise BaseException('ChromeDriver not found')


def normalize_name(name):
    return normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()


def make_google_cache_url(name):
    return 'http://webcache.googleusercontent.com/search?btnG=Search&q=cache:www.consultasocio.com/q/sa/%s' % \
           normalize_name(name).replace(' ', '-')


def make_consulta_socio_url(name):
    return 'http://www.consultasocio.com/q/sa/%s' % normalize_name(name).replace(' ', '-')


def extract_info_from_page(url, info, driver, error_msg):
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
    if error_msg.lower() not in soup.title.text.lower():
        for partner in soup.findAll('span', attrs={'class': 'socio'}):
            info['partners'].append(partner.text)
        for company_info in soup.findAll('p', attrs={'class': 'number'}):
            info['business'].append(company_info.find('span', {'class': 'text'}).text)
        try:
            info['cache_info'] = soup.find('div', attrs={'id': 'google-cache-hdr'}).text
        except:
            info['cache_info'] = str(datetime.datetime.now())
        print(info)
        return info


def fetch_business_infos():
    file_base_name = '{}-congressperson-business-partners.json'.format(datetime.date.today().strftime('%Y-%m-%d'))
    output_file_path = os.path.join(os.path.abspath('../data'), file_base_name)

    # Load cached data if file exists
    result = {}
    if os.path.exists(output_file_path):
        result = json.loads(open(output_file_path, 'r').read())

    # Collect the information from all congress person
    civil_names_df = pd.read_csv('../data/2016-12-07-congressperson-civil-names.xz')

    driver = webdriver.Chrome(selenium_driver_path())

    original_site_blocked = False
    id = 0
    collected_count = 0
    total_count = len(civil_names_df['civil_name'].unique())
    for name in civil_names_df['civil_name'].unique():
        name = normalize_name(name).upper()

        print('(%d/%d) %s' % (id, total_count, name), sep=' ', end='\n')
        if name in result:
            collected_count += 1
        else:
            default_info = {'partners': [], 'business': []}
            if not original_site_blocked:
                info = extract_info_from_page(make_consulta_socio_url(name), default_info, driver,
                                              'Uso — ConsultaSocio.com')
                original_site_blocked = info is None
            if info is None:
                info = extract_info_from_page(make_google_cache_url(name), default_info, driver, 'error')
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
    fetch_business_infos()
