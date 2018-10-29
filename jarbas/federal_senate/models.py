from django.db import models
from django.contrib.postgres.fields import JSONField


class Reimbursement(models.Model):
    document_id = models.CharField('Número do Reembolso', max_length=140, blank=True, null=True)
    last_update = models.DateTimeField('Atualizado no Jarbas em', db_index=True, auto_now=True)

    year = models.IntegerField('Ano', db_index=True)
    month = models.IntegerField('Mês', db_index=True)
    date = models.DateField('Data', db_index=True)

    congressperson_name = models.CharField('Nome do Parlamentar', max_length=140, db_index=True, blank=True, null=True)

    expense_type = models.CharField('Tipo da Despesa', max_length=140, blank=True, null=True)
    expense_details = models.CharField('Descrição da Despesa', max_length=140, blank=True, null=True)

    supplier = models.CharField('Fornecedor', max_length=256)
    cnpj_cpf = models.CharField('CNPJ ou CPF', max_length=14, db_index=True, blank=True, null=True)

    reimbursement_value = models.DecimalField('Valor do Reembolso', max_digits=10, decimal_places=3, blank=True, null=True)

    probability = models.DecimalField('Probabilidade', max_digits=6, decimal_places=5, blank=True, null=True)
    suspicions = JSONField('Suspeitas', blank=True, null=True)

    class Meta:
        ordering = ('-year', '-date')
        verbose_name = 'reembolso'
        verbose_name_plural = 'reembolsos'
        index_together = [['year', 'date', 'id']]
