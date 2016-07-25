# Lista de Dados Públicos e Estratégias para Coleta em Massa

| Informação | Motivo | Estratégia |
|------------|--------|------------|
| [Cota para Exercício da Atividade Parlamentar](http://www.camara.gov.br/cota-parlamentar/) (Deputados Federais) | Listar gastos de deputados federais | Data scraping |
| [Cota para Exercício da Atividade Parlamentar](http://www25.senado.leg.br/web/transparencia/sen/) (Senadores) | Listar gastos de senadores | Data scraping |
| [Consulta de CNPJ na Receita Federal](http://www.receita.fazenda.gov.br/pessoajuridica/cnpj/cnpjreva/cnpjreva_solicitacao.asp) | Levantar informações sobre onde foi gasto o dinheiro público | Captcha. (testar [API “alternativa” sem captcha](http://receitaws.com.br) e estudar viabilidade) |
| [Google Street View](https://developers.google.com/maps/documentation/streetview/) | Identificar se o endereço é comercial ou residencial | API |
| [Estimativa do alugel de imóveis](ftp://ftp.ibge.gov.br/Contas_Nacionais/Sistema_de_Contas_Nacionais/Notas_Metodologicas_2010/06_aluguel.pdf) | Comparar o preço em notas fiscais com o valor do metro quadrado na área. | Scraping de dados de [estudo do IBGE](http://seriesestatisticas.ibge.gov.br/series.aspx?vcodigo=PRECO415). |
| [Facebook Graph API](https://developers.facebook.com/docs/graph-api) | Identificar se duas pessoas se conhecem |  _Pendente_: [API mostra apenas amigos com o mesmo _app_ instalado](https://developers.facebook.com/docs/graph-api/reference/user/friends/).


# Public Data Lists and Strategies for Mass Collection

| Information | Reason | Strategy |
|------------|--------|------------|
| [Quota for exercising Parliamentary Activity](http://www.camara.gov.br/cota-parlamentar/) (Federal Deputies) | List expenses of federal deputies | Data scraping |
| [Quota for exercising Parliamentary Activity](http://www25.senado.leg.br/web/transparencia/sen/) (Senators) | List expenses of senators | Data scraping |
| [CNPJ consultation with the Federal Revenue](http://www.receita.fazenda.gov.br/pessoajuridica/cnpj/cnpjreva/cnpjreva_solicitacao.asp) | Gather information on where public money was spent | Captcha. (test [“alternative” API without captcha](http://receitaws.com.br) and assess viability) |
| [Google Street View](https://developers.google.com/maps/documentation/streetview/) | Identify whether the address is residential or commercial | API |
| [Lease sale estimation of real estate](ftp://ftp.ibge.gov.br/Contas_Nacionais/Sistema_de_Contas_Nacionais/Notas_Metodologicas_2010/06_aluguel.pdf) | Compare the price on invoices to the value of square meter in the area. | Data scraping from [a study by IBGE](http://seriesestatisticas.ibge.gov.br/series.aspx?vcodigo=PRECO415). |
| [Facebook Graph API](https://developers.facebook.com/docs/graph-api) | Identify if two people know eachother |  _Pending_: [API shows just friends with the same app installed.](https://developers.facebook.com/docs/graph-api/reference/user/friends/).
