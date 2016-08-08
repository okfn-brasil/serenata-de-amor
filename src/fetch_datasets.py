import subprocess
from urllib.request import urlretrieve

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
            'data/datasets_format.html')
