from django.core.cache import cache
from django.contrib.admin import SimpleListFilter

from jarbas.chamber_of_deputies.models import Reimbursement
from jarbas.dashboard.admin.subquotas import Subquotas


class CachedListFilter(SimpleListFilter):

    timeout = 60 * 60 * 6  # 6h

    def lookups(self, request, model_admin):
        cached = cache.get(self.cache_key)
        if cached:
            return cached

        queryset = Reimbursement.objects.distinct(self.parameter_name) \
            .order_by(self.parameter_name) \
            .values_list(self.parameter_name, self.parameter_name)

        value = tuple(state for state in queryset if all(state))
        cache.set(self.cache_key, value, self.timeout)
        return value

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        kwarg = {self.parameter_name: value}
        return queryset.filter(**kwarg)


class JarbasListFilter(SimpleListFilter):

    options = tuple()

    def lookups(self, request, model_admin):
        return self.options

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        kwarg = {self.parameter_name: self.value()}
        return queryset.filter(**kwarg)


class SuspiciousListFilter(JarbasListFilter):

    title = 'reembolso suspeito'
    parameter_name = 'is_suspicions'
    options = (
        ('yes', 'Sim'),
        ('no', 'Não'),
    )

    def queryset(self, request, queryset):
        filter_option = {
            'yes': queryset.suspicions(True),
            'no': queryset.suspicions(False)
        }
        return filter_option.get(self.value(), queryset)


class HasReceiptFilter(JarbasListFilter):

    title = 'nota fiscal digitalizada'
    parameter_name = 'has_receipt'
    options = (
        ('yes', 'Sim'),
        ('no', 'Não'),
    )

    def queryset(self, request, queryset):
        receipt_url_filter = {
            'yes': queryset.has_receipt_url(True),
            'no': queryset.has_receipt_url(False)
        }
        return receipt_url_filter.get(self.value(), queryset)


class MonthListFilter(JarbasListFilter):

    title = 'mês'
    parameter_name = 'month'
    options = (
        (1, 'Janeiro'),
        (2, 'Fevereiro'),
        (3, 'Março'),
        (4, 'Abril'),
        (5, 'Maio'),
        (6, 'Junho'),
        (7, 'Julho'),
        (8, 'Agosto'),
        (9, 'Setembro'),
        (10, 'Outubro'),
        (11, 'Novembro'),
        (12, 'Dezembro')
    )


class DocumentTypeListFilter(JarbasListFilter):

    title = 'tipo do documento fiscal'
    parameter_name = 'document_type'
    options = (
        (0, 'Nota fiscal'),
        (1, 'Recibo simples'),
        (2, 'Despesa no exterior')
    )


class SubquotaListFilter(SimpleListFilter, Subquotas):

    title = 'subcota'
    parameter_name = 'subquota_number'
    default_value = None

    def lookups(self, request, model_admin):
        return self.OPTIONS

    def queryset(self, request, queryset):
        subquota = dict(self.OPTIONS).get(self.value())
        if not subquota:
            return queryset
        return queryset.filter(subquota_description=self.en_us(subquota))


class StateListFilter(CachedListFilter):

    title = 'estado'
    parameter_name = 'state'
    default_value = None
    cache_key = 'dashboard_state_list_filter_lookups'


class YearListFilter(CachedListFilter):

    title = 'ano'
    parameter_name = 'year'
    default_value = None
    cache_key = 'dashboard_year_list_filter_lookups'
