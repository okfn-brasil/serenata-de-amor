import csv
import datetime
import os
from lxml import html

import grequests
import requests

CAMARA_URL = 'http://www2.camara.leg.br/transparencia/recursos-humanos/quadro-remuneratorio/consulta-secretarios-parlamentares/layouts_transpar_quadroremuner_consultaSecretariosParlamentares'
USERAGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data')
DATE = datetime.date.today().strftime('%Y-%m-%d')
FILE_BASE_NAME = '{}-deputies-advisors.csv'.format(DATE)

def run():
    print("Fetching deputies data...")
    deputies_data = fetch_deputies_data()

    print("Preparing requests to fetch advisors data...")
    requests = [get_request_to_page_of_advisors_from_deputy(deputy) for deputy in deputies_data]

    for page_data in send_requests(requests):
        deputy_with_advisors = page_data["data"]
        deputy_information = organize_deputy_data({"deputy_name": deputy_with_advisors["deputy_name"], "deputy_number": deputy_with_advisors["deputy_number"]}, deputy_with_advisors["deputy_advisors"])
        write_to_csv(deputy_information, os.path.join(DATA_PATH, FILE_BASE_NAME))

    print("\nFinished! The file can be found at data/{}".format(FILE_BASE_NAME))


def send_requests(reqs):
    """
    Send all the requests in :reqs: and reads the response data to extract the deputies data.
    It will check if a deputy has more than one page of advisors and send new requests if True
    """
    request_buffer = list()

    print("Sending!")
    for response in grequests.imap(reqs, size=8, exception_handler=http_exception_handler):
        page_data = extract_data_from_page(response)

        yield page_data
        print('.', end="", flush=True)

        if page_data["has_next_page"]:
            for rq in [get_request_to_page_of_advisors_from_deputy(page_data['data'], page_number) for page_number in range(page_data["current_page"], page_data["number_of_pages"])]:
                request_buffer.append(rq)

    print("\nFound {} more pages to fetch. Starting now...".format(len(request_buffer)))
    for req in grequests.imap(request_buffer, size=8, exception_handler=http_exception_handler):
        page_data = extract_data_from_page(req)

        yield page_data
        print(':', end="", flush=True)


def fetch_deputies_data():
    """
    Returns a list with all deputies names and its numbers after parsing the `<select>` element in `CAMARA_URL`
    """
    page = requests.get(CAMARA_URL)
    tree = html.fromstring(page.content)

    deputies_data = [{"deputy_name": element.xpath("./text()")[0], "deputy_number": element.xpath('./@value')[0]} for element in tree.xpath('//select[@id="lotacao"]/option')]

    return deputies_data[1:] # removing the first element: it's the "Selecione um deputado" option.


def get_request_to_page_of_advisors_from_deputy(deputy, page=1):
    """
    Returns a POST AsyncRequest object from grequests ready to be sent to `CAMARA_URL` with `lotacao` field filled with `deputy_number`
    Some deputies can have more than 20 advisors, so some pages will have pagination.
    In this case it's necessary to inform the specific page you want to create a request to, otherwise a request to the first page will be created.
    :deputy: (dict) A Dict with fields `deputy_name` and `deputy_number`
    :page: (int) Defaults to 1. The page number
    """
    params = {"lotacao": deputy["deputy_number"],"b_start:int": 0 if page==1 else 20 + (page - 2) * 20} # page 1 = 0, page 2 = 20, page 3 = 40, ...
    return grequests.post(CAMARA_URL, data=params)


def extract_data_from_page(page):
    """
    Extracts all relevant data from a page and returns it as Dict.
    Each information is inside a key in the dict as following:
    - Deputy name, number and advisors inside the key `data` as `deputy_name`, `deputy_number` and `deputy_advisors` respectively.
    - Number of pages of advisors; as `number_of_pages`
    - the current page number as `current_page`
    - if it has more pages of advisors as `has_next_page`
    """
    html_tree = html.fromstring(page.content)

    number_of_pages = extract_number_of_pages(html_tree)
    current_page = extract_current_page(html_tree)
    select = html_tree.xpath('//select[@id="lotacao"]/option[@selected]')[0]
    deputy_advisors = [element.xpath('./td/text() | ./td/span/text()') for element in html_tree.xpath('//tbody[@class="coresAlternadas"]/tr')]

    # Some "Data de Publicação do Ato" are empty in `CAMARA_URL` and xpath are not adding an 'empty string' inside the returned array, so we are adding it manualy below
    for advisor_info in deputy_advisors:
        if len(advisor_info) == 3:
            advisor_info.append("Empty")
    # End

    return {
        'data': {
            "deputy_name": select.xpath('./text()')[0], "deputy_number": select.xpath("./@value")[0], "deputy_advisors": deputy_advisors
        },
        'number_of_pages': number_of_pages,
        'current_page': current_page,
        'has_next_page': False if current_page == number_of_pages else True
    }


def extract_current_page(tree):
    """
    Helper function to extract the current page number of the page of advisors from a HTMLElement (lxml)
    """
    result = tree.xpath('//ul[@class="pagination"]/li[@class="current"]/span/text()')
    return 1 if len(result) == 0 else int(result[0])


def extract_number_of_pages(tree):
    """
    Helper function to extract the number of pages of the page of advisors from a HTMLElement (lxml)
    """
    result = tree.xpath('count(//ul[@class="pagination"]/li[not(contains(@class,"next"))][not(contains(@class,"previous"))])')
    return 1 if result == 0 else int(result)


def organize_deputy_data(deputy, advisors):
    """
    Organizes all the deputies information in a list. Use this function to prepare data to be written to CSV format.
    :deputy: (Dict) A dict with keys `deputy_name` and `deputy_number`
    :advisors: (list) A list of lists with advisors data.
    """
    output = list()
    if len(advisors) == 0:
        output.append(["","","","", deputy["deputy_name"], deputy["deputy_number"]])
        return output
    else:
        for dep in advisors:
            output.append(dep[:] + [deputy["deputy_name"], deputy["deputy_number"]])

    return output


def write_to_csv(data, output):
    """
    Writes `data` to `output`
    :data: (list) the list with organized deputy information ready to be written
    :output: (string) the full path to a file where :data: should be written
    """
    with open(output, "a", newline="") as latest_file:
        fieldnames = ['ponto', 'nome', 'data_de_publicacao_do_ato', 'orgao_de_origem', 'deputy_name', 'deputy_number']
        writer = csv.DictWriter(latest_file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        for advisor in data:
            writer.writerow({'ponto': advisor[0], 'nome': advisor[1], 'data_de_publicacao_do_ato': advisor[2],'orgao_de_origem': advisor[3], 'deputy_name': advisor[4], 'deputy_number': advisor[5]})


def http_exception_handler(request, exception):
    """
    Callback to be executed by grequests when a request fails
    """
    print(exception)

if __name__ == '__main__':
    run()

