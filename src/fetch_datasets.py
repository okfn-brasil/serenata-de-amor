from urllib.request import urlretrieve

dataset_urls = [
    'http://www.camara.gov.br/cotas/AnoAtual.zip',
    'http://www.camara.gov.br/cotas/AnoAnterior.zip',
    'http://www.camara.gov.br/cotas/AnosAnteriores.zip']
filenames = map(lambda url: url.split('/')[-1], dataset_urls)

for url, filename in zip(dataset_urls, filenames):
    urlretrieve(url, 'data/%s' % filename)
