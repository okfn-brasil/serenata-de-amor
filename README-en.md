# Serenata de amor
> Fighting corruptions in a massive and effective way

[🇧🇷 Ir para versão em Português](README.md)

The idea of automating the analysis of public accounts is unprecedented: engaging the population on training our platform in the analysis and audit. After this initial stage automation enhances data analysis in unseen volumes, increasing the chances of finding mistakes and corruption.

In other words, the Machine Learning platform invites people to teach it, learn from it, and massively expands existing methods. Alongside the production of content and a user friendly interface to explore data, expand access to information. Crowdsourcing the analysis of what is done with public money and exposure of these analyses openly, the whole society will have arguments to press politicians and demand that diverted money to be returned to public coffers.

In the background this movement helps to create a more clear perspective about the political activity of the parliament, making everyone of us have a better idea on deciding who to vote in the next election.

## Support the project with money

Unlike the politicians we investigate, we don't get fortunes in a daily basis. But maintaining infrastructure and a team working on the project costs money. Want to contribute?

[Bitcoin Wallet](bitcoin:1Gg9CVZNYmzMTAjGfMg62w3b6MM7D1UAUV?amount=0.01&message=Supporting%20project%20Serenata%20de%20Amor)
```
1Gg9CVZNYmzMTAjGfMg62w3b6MM7D1UAUV
```

## Public Data Lists and Strategies for Mass Collection

### Data scraping
| Information | Reason | Strategy |
|------------|--------|------------|
| [Quota for exercising Parliamentary Activity](http://www.camara.gov.br/cota-parlamentar/) (Federal Deputies) | List expenses of federal deputies | Data scraping |
| [Quota for exercising Parliamentary Activity](http://www25.senado.leg.br/web/transparencia/sen/) (Senators) | List expenses of senators | Data scraping |
| [Lease sale estimation of real estate](ftp://ftp.ibge.gov.br/Contas_Nacionais/Sistema_de_Contas_Nacionais/Notas_Metodologicas_2010/06_aluguel.pdf) | Compare the price on invoices to the value of square meter in the area. | Data scraping from [a study by IBGE](http://seriesestatisticas.ibge.gov.br/series.aspx?vcodigo=PRECO415). |

### API
| Information | Reason | Strategy |
|------------|--------|------------|
| [Google Street View](https://developers.google.com/maps/documentation/streetview/) | Identify whether the address is residential or commercial | API |
| [CNPJ consultation with the Federal Revenue](http://www.receita.fazenda.gov.br/pessoajuridica/cnpj/cnpjreva/cnpjreva_solicitacao.asp) | Gather information on where public money was spent | Captcha. (test [“alternative” API without captcha](http://receitaws.com.br) and assess viability) |
| [Facebook Graph API](https://developers.facebook.com/docs/graph-api) | Identify if two people know eachother |  _Pending_: [API shows just friends with the same app installed.](https://developers.facebook.com/docs/graph-api/reference/user/friends/).

## Contribute
Please read and follow our **[contributing guidelines](CONTRIBUTING.md)**.
