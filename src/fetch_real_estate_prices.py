from urllib.request import urlretrieve

urls = [
    ('region', 'http://seriesestatisticas.ibge.gov.br/exportador.aspx?arquivo=PRECO415_GR_ABS.csv&localidade=Todas'),
    ('state', 'http://seriesestatisticas.ibge.gov.br/exportador.aspx?arquivo=PRECO415_UF_ABS.csv&localidade=Todas'),
    ('brasil', 'http://seriesestatisticas.ibge.gov.br/exportador.aspx?arquivo=PRECO415_BR_ABS.csv',)]


for (by, url) in urls:
    urlretrieve(url, 'data/average_real_estate_prices_by_%s.csv' % by)
