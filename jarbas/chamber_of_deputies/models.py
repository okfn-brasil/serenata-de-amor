from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from requests import head

from simple_history.models import HistoricalRecords
from jarbas.chamber_of_deputies.querysets import ReimbursementQuerySet


class Receipt:

    def __init__(self, year, applicant_id, document_id):
        self.year = year
        self.applicant_id = applicant_id
        self.document_id = document_id

    @property
    def url(self):
        args = (self.applicant_id, self.year, self.document_id)
        return (
            'http://www.camara.gov.br/'
            'cota-parlamentar/documentos/publ/{}/{}/{}.pdf'
        ).format(*args)

    @property
    def exists(self):
        status = head(self.url).status_code
        return 200 <= status < 400


class Reimbursement(models.Model):
    document_id = models.IntegerField('Número do Reembolso', db_index=True, unique=True)
    last_update = models.DateTimeField('Atualizado no Jarbas em', db_index=True, auto_now=True)
    available_in_latest_dataset = models.BooleanField('Disponível na Câmara dos Deputados', default=True)

    year = models.IntegerField('Ano', db_index=True)
    applicant_id = models.IntegerField('Identificador do Solicitante', db_index=True)

    total_reimbursement_value = models.DecimalField('Valor da Restituição', max_digits=10, decimal_places=3, blank=True, null=True)
    total_net_value = models.DecimalField('Valor Líquido', max_digits=10, decimal_places=3)
    reimbursement_numbers = models.CharField('Números dos Ressarcimentos', max_length=140)
    net_values = models.CharField('Valores Líquidos dos Ressarcimentos', max_length=140)

    congressperson_id = models.IntegerField('Identificador Único do Parlamentar', blank=True, null=True)
    congressperson_name = models.CharField('Nome do Parlamentar', max_length=140, db_index=True, blank=True, null=True)
    congressperson_document = models.IntegerField('Número da Carteira Parlamentar', blank=True, null=True)

    party = models.CharField('Partido', max_length=7, blank=True, null=True)
    state = models.CharField('UF', max_length=2, db_index=True, blank=True, null=True)

    term_id = models.IntegerField('Código da Legislatura', blank=True, null=True)
    term = models.IntegerField('Número da Legislatura', blank=True, null=True)

    subquota_id = models.IntegerField('Número da Subcota', db_index=True)
    subquota_description = models.CharField('Descrição da Subcota', max_length=140, db_index=True)
    subquota_group_id = models.IntegerField('Número da Especificação da Subcota', blank=True, null=True)
    subquota_group_description = models.CharField('Descrição da Especificação da Subcota', max_length=140, blank=True, null=True)

    supplier = models.CharField('Fornecedor', max_length=140)
    cnpj_cpf = models.CharField('CNPJ ou CPF', max_length=14, db_index=True, blank=True, null=True)

    document_type = models.IntegerField('Indicativo de Tipo de Documento Fiscal')
    document_number = models.CharField('Número do Documento', max_length=140, blank=True, null=True)
    document_value = models.DecimalField('Valor do Documento', max_digits=10, decimal_places=3)

    issue_date = models.DateField('Data de Emissão', db_index=True)
    month = models.IntegerField('Mês', db_index=True)
    remark_value = models.DecimalField('Valor da Glosa', max_digits=10, decimal_places=3, blank=True, null=True)
    installment = models.IntegerField('Número da Parcela', blank=True, null=True)
    batch_number = models.IntegerField('Número do Lote')
    reimbursement_values = models.CharField('Valores dos Ressarcimentos', max_length=140, blank=True, null=True)

    passenger = models.CharField('Passageiro', max_length=140, blank=True, null=True)
    leg_of_the_trip = models.CharField('Trecho', max_length=140, blank=True, null=True)

    probability = models.DecimalField('Probabilidade', max_digits=6, decimal_places=5, blank=True, null=True)
    suspicions = JSONField('Suspeitas', blank=True, null=True)

    receipt_fetched = models.BooleanField('Tentamos acessar a URL do documento fiscal?', default=False, db_index=True)
    receipt_url = models.CharField('URL do Documento Fiscal', max_length=140, blank=True, null=True)
    receipt_text = models.TextField('Texto do Recibo', blank=True, null=True)

    search_vector = SearchVectorField(null=True)

    history = HistoricalRecords()

    objects = models.Manager.from_queryset(ReimbursementQuerySet)()

    class Meta:
        ordering = ('-year', '-issue_date')
        verbose_name = 'reembolso'
        verbose_name_plural = 'reembolsos'
        index_together = [['year', 'issue_date', 'id']]
        indexes = [GinIndex(fields=['search_vector'])]

    def get_receipt_url(self, force=False, bulk=False):
        if self.receipt_url:
            return self.receipt_url

        if self.receipt_fetched and not force:
            return None

        receipt = Receipt(self.year, self.applicant_id, self.document_id)
        if receipt.exists:
            self.receipt_url = receipt.url
        self.receipt_fetched = True

        if bulk:
            return self

        self.save()
        return self.receipt_url

    @property
    def all_net_values(self):
        return self.as_list(self.net_values, float)

    @property
    def all_reimbursement_values(self):
        return self.as_list(self.reimbursement_values, float)

    @property
    def all_reimbursement_numbers(self):
        return self.as_list(self.reimbursement_numbers, int)

    @staticmethod
    def as_list(content, cast=None):
        if not content:
            return None

        parts = content.split(',')
        return [cast(p) for p in parts] if cast else parts

    def __repr__(self):
        return 'Reimbursement(document_id={})'.format(self.document_id)

    def __str__(self):
        return 'Documento nº {}'.format(self.document_id)


class Tweet(models.Model):

    reimbursement = models.OneToOneField(Reimbursement)
    status = models.DecimalField('Tweet ID', db_index=True, max_digits=25, decimal_places=0)

    def get_url(self):
        base_url = 'https://twitter.com/RosieDaSerenata/status/'
        return base_url + str(self.status)

    def __str__(self):
        return self.get_url()

    def __repr__(self):
        return '<Tweet: status={}>'.format(self.status)

    class Meta:
        ordering = ('-status',)
