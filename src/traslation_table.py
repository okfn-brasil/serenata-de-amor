from bs4 import BeautifulSoup

HEADERS = (
    '🇧🇷Variable',
    '🇧🇷Name',
    '🇧🇷Description',
    '🇬🇧Variable',
    '🇬🇧Name',
    '🇬🇧Description'
)

EN = (
    {
        'variable': 'congressperson_name',
        'name': 'Congressperson Name',
        'description': """Nome adotado pelo Parlamentar ao tomar posse do seu
            mandato.  Compõe-se de dois elementos: um prenome e o nome; dois
            nomes; ou dois prenomes, salvo, a juízo do Presidente da Casa
            legislativa, que poderá alterar essa regra para que não ocorram
            confusões."""
    },
    {
        'variable': 'congressperson_id',
        'name': 'Unique Identifier of Congressperson',
        'description': """Número que identifica unicamente um deputado federal
            na CD."""
    },
    {
        'variable': 'congressperson_document',
        'name': 'Congressperson Document Number',
        'description': """Documento usado para identificar um deputado federal
            na CD. Pode alt """
    },
    {
        'variable': 'term',
        'name': 'Legislative Period Number',
        'description': """Legislatura: Período de quatro anos coincidente com o
            mandato parlamentar dos Deputados Federais. No contexto da cota
            CEAP, representa o ano base de início da legislatura e é utilizado
            para compor a Carteira Parlamentar, pois esta poderá ser alterada à
            medida que se muda de Legislatura."""
    },
    {
        'variable': 'state',
        'name': 'State',
        'description': """No contexto da cota CEAP, representa a unidade da
            federação pela qual o deputado foi eleito e é utilizada para
            definir o valor da cota a que o deputado tem."""
    },
    {
        'variable': 'party',
        'name': 'Party',
        'description': """O seu conteúdo representa a sigla de um partido.
            Definição de partido: é uma organização formada por pessoas com
            interesse ou ideologia comuns, que se associam com o fim de assumir
            o poder para implantar um programa de governo. Tem personalidade
            jurídica de direito privado e goza de autonomia e liberdade no que
            diz respeito à criação, organização e funcionamento, observados os
            princípios e preceitos constitucionais."""
    },
    {
        'variable': 'term_id',
        'name': 'Legislative Period Code',
        'description': """Legislatura: Período de quatro anos coincidente com o
            mandato parlamentar dos Deputados Federais. No contexto da cota
            CEAP, o seu conteúdo representa o código identificador da
            Legislatura, que um número ordinal sequencial, alterado de um em
            um, a cada início de uma nova Legislatura (por exemplo, a
            Legislatura que iniciou em 2011 é a 54ª Legislatura)."""
    },
    {
        'variable': 'subquota_number',
        'name': 'Subquota Number',
        'description': """No contexto da Cota CEAP, o conteúdo deste dado
            representa o código do Tipo de Despesa referente à despesa
            realizada pelo deputado e comprovada por meio da emissão de um
            documento fiscal, a qual é debitada na cota do deputado."""
    },
    {
        'variable': 'subquota_description',
        'name': 'Subquota Description',
        'description': """O seu conteúdo é a descrição do Tipo de Despesa
            relativo à despesa em questão."""
    },
    {
        'variable': 'subquota_group_id',
        'name': 'Subquota Specification Number',
        'description': """No contexto da Cota CEAP, há despesas cujo Tipo de
            Despesa necessita ter uma especificação mais detalhada (por
            exemplo, “Combustível”). O conteúdo deste dado representa o código
            desta especificação mais detalhada."""
    },
    {
        'variable': 'subquota_group_description',
        'name': 'Subquota Specification Description',
        'description': """Representa a descrição  especificação mais detalhada
            de um referido Tipo de Despesa."""
    },
    {
        'variable': 'supplier',
        'name': 'Supplier',
        'description': """O conteúdo deste dado representa o nome do
            fornecedor do produto ou serviço presente no documento fiscal"""
    },
    {
        'variable': 'cnpj_cpf',
        'name': 'CNPJ/CPF',
        'description': """O conteúdo deste dado representa o CNPJ ou o CPF do
            emitente do documento fiscal, quando se tratar do uso da cota em
            razão do reembolso despesas comprovadas pela emissão de documentos
            fiscais."""
    },
    {
        'variable': 'document_number',
        'name': 'Document Number',
        'description': """O conteúdo deste dado representa o número de face do
            documento fiscal emitido ou o número do documento que deu causa à
            despesa debitada na cota do deputado."""
    },
    {
        'variable': 'document_type',
        'name': 'Fiscal Document Type',
        'description': """Este dado representa o tipo de documento do fiscal –
            0 (Zero), para Nota Fiscal; 1 (um), para Recibo; e 2, para Despesa
            no Exterior. """
    },
    {
        'variable': 'issue_date',
        'name': 'Issue Date',
        'description': """O conteúdo deste dado é a data de emissão do
            documento fiscal ou a data do documento que tenha dado causa à
            despesa. """
    },
    {
        'variable': 'document_value',
        'name': 'Document Value',
        'description': """O seu conteúdo é o valor de face do documento fiscal
            ou o valor do documento que deu causa à despesa. Quando se tratar
            de bilhete aéreo, esse valor poderá ser negativo, significando que
            o referido bilhete é um bilhete de compensação, pois compensa um
            outro bilhete emitido e não utilizado pelo deputado (idem para o
            dado vlrLiquido abaixo). """
    },
    {
        'variable': 'remark_value',
        'name': 'Remark Value',
        'description': """O seu conteúdo representa o valor da glosa do
            documento fiscal que incidirá sobre o Valor do Documento, ou o
            valor da glosa do documento que deu causa à despesa. """
    },
    {
        'variable': 'net_value',
        'name': 'Net Value',
        'description': """O seu conteúdo representa o valor líquido do
            documento fiscal ou do documento que deu causa à despesa e será
            calculado pela diferença entre o Valor do Documento e o Valor da
            Glosa. É este valor que será debitado da cota do deputado. Caso o
            débito seja do Tipo Telefonia e o valor seja igual a zero,
            significa que a despesa foi franqueada. """
    },
    {
        'variable': 'month',
        'name': 'Month',
        'description': """O seu conteúdo representa o Mês da competência
            financeira do documento fiscal ou do documento que deu causa à
            despesa. É utilizado, junto com o ano, para determinar em que
            período o débito gerará efeito financeiro sobre a cota. """
    },
    {
        'variable': 'year',
        'name': 'Year',
        'description': """O seu conteúdo representa o Ano da competência
            financeira do documento fiscal ou do documento que deu causa à
            despesa. É utilizado, junto com o mês, para determinar em que
            período o débito gerará efeito financeiro sobre a cota. """
    },
    {
        'variable': 'installment',
        'name': 'Installment Number',
        'description': """O seu conteúdo representa o número da parcela do
            documento fiscal. Ocorre quando o documento tem de ser reembolsado
            de forma parcelada. """
    },
    {
        'variable': 'passenger',
        'name': 'Passenger',
        'description': """O conteúdo deste dado representa o nome do passageiro
            , quando o documento que deu causa à despesa se tratar de emissão
            de bilhete aéreo. """
    },
    {
        'variable': 'leg_of_the_trip',
        'name': 'Leg of the Trip',
        'description': """O conteúdo deste dado representa o trecho da viagem,
            quando o documento que deu causa à despesa se tratar de emissão de
            bilhete aéreo. """
    },
    {
        'variable': 'batch_number',
        'name': 'Batch Number',
        'description': """No contexto da Cota CEAP, o Número do Lote
            representa uma capa de lote que agrupa os documentos que serão
            entregues à Câmara para serem ressarcidos. Este dado, juntamente
            com o Número do Ressarcimento, auxilia a localização do documento
            no Arquivo da Casa. """
    },
    {
        'variable': 'reimbursement_number',
        'name': 'Reimbursement Number',
        'description': """No contexto da Cota CEAP, o Número do Ressarcimento
            indica o ressarcimento do qual o documento fez parte por ocasião
            do processamento do seu reembolso. Este dado, juntamente com o
            Número do Ressarcimento, auxilia a localização do documento no
            Arquivo da Casa. """
    },
    {
        'variable': 'reimbursement_value',
        'name': 'Reimbursement Value',
        'description': """O seu conteúdo representa o valor restituído do
            documento fiscal que incidirá sobre o Valor do Documento. """
    },
    {
        'variable': 'applicant_id',
        'name': 'Applicant Identifier',
        'description': """Número que identifica um Parlamentar ou Liderança na
            Transparência da Cota para Exercício da Atividade Parlamentar. """
    }
)


def get_portuguese():
    """
    Returns a list of dicionaries with variable, name and description in pt-BR
    (based on data/datasets_format.html)
    """
    with open('data/datasets_format.html', 'rb') as file_handler:
        parsed = BeautifulSoup(file_handler.read(), 'lxml')
        for row in parsed.select('.tabela-2 tr'):
            cells = row.select('td')
            if cells:
                var, name, desc = map(lambda x: x.text.strip(), cells)
                yield {
                    'variable': var,
                    'name': name,
                    'description': desc
                }


def get_lines():
    """Merges EN and PT versions in a single tuple of tuples"""
    fields = ('variable', 'name', 'description')
    for pt, en in zip(get_portuguese(), EN):
        yield tuple([pt[f] for f in fields] + [en[f] for f in fields])


def markdown():
    yield '# Dataset variables and descrition translation table\n'
    yield '| {} |'.format(' | '.join(HEADERS))
    yield '|---|---|---|---|---|'
    for line in get_lines():
        cleaned = map(lambda x: x.replace('\n', ''), line)
        yield '| {} |'.format(' | '.join(cleaned))

with open('data/dataset_translation_table.md', 'w') as file_handler:
    file_handler.write('\n'.join(markdown()))
