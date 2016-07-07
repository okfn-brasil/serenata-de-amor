# Lista de dados públicos e estratégias para coleta em massa

| Informação | Motivo | Estratégia |
|------------|--------|------------|
| [Cota para Exercício da Atividade Parlamentar](http://www.camara.gov.br/cota-parlamentar/) (Deputados Federais) | Listar gastos de deputados federais | Data scraping |
| [Cota para Exercício da Atividade Parlamentar](http://www25.senado.leg.br/web/transparencia/sen/) (Senadores) | Listar gastos de senadores | Data scraping |
| [Consulta de CNPJ na Receita Federal](http://www.receita.fazenda.gov.br/pessoajuridica/cnpj/cnpjreva/cnpjreva_solicitacao.asp) | Levantar informações sobre onde foi gasto o dinheiro público | Captcha. (testar [API “alternativa” sem captcha](http://receitaws.com.br) e estudar viabilidade) |
| [Google Street View](https://developers.google.com/maps/documentation/streetview/) | Identificar se o endereço é comercial ou residencial | API |
| [Estimativa do alugel de imóveis](ftp://ftp.ibge.gov.br/Contas_Nacionais/Sistema_de_Contas_Nacionais/Notas_Metodologicas_2010/06_aluguel.pdf) | Comparar o preço em notas fiscais com o valor do metro quadrado na área. | Scraping de dados de [estudo do IBGE](http://seriesestatisticas.ibge.gov.br/series.aspx?vcodigo=PRECO415). |
| [Facebook Graph API](https://developers.facebook.com/docs/graph-api) | Identificar se duas pessoas se conhecem |  _Pendente_: [API mostra apenas amigos com o mesmo _app_ instalado](https://developers.facebook.com/docs/graph-api/reference/user/friends/).
