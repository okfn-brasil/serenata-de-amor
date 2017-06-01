from brazilnum.cnpj import format_cnpj
from brazilnum.cpf import format_cpf
from django.contrib.admin import SimpleListFilter
from simple_history.admin import SimpleHistoryAdmin

from jarbas.core.models import Reimbursement
from jarbas.dashboard.sites import dashboard


class SuspiciousListFilter(SimpleListFilter):

    title = 'Is suspicious'

    parameter_name = 'is_suspicions'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no',  'No'),
        )

    def queryset(self, request, queryset):
        return queryset.suspicions() if self.value() == 'yes' else queryset


class ReimbursementModelAdmin(SimpleHistoryAdmin):

    list_display = (
        'short_document_id',
        'jarbas',
        'congressperson_name',
        'year',
        'subquota_description',
        'is_suspicious',
        'supplier_info',
        'value',
        'still_available',
    )
    search_fields = (
        'applicant_id',
        'cnpj_cpf',
        'congressperson_name',
        'document_id',
        'party',
        'state',
        'supplier',
        'subquota_description',
    )
    list_filter = (
        SuspiciousListFilter,
        'available_in_latest_dataset',
        'state',
        'year',
        'subquota_description',
    )
    readonly_fields = tuple(f.name for f in Reimbursement._meta.fields)
    has_permission = dashboard.has_permission

    def has_add_permission(self, request):
        return False
    def _format_document(self, obj):
        if len(obj.cnpj_cpf) == 14:
            return format_cnpj(obj.cnpj_cpf)

    def has_change_permission(self, request, obj=None):
        if request.method != 'GET':
            return False
        return True
        if len(obj.cnpj_cpf) == 11:
            return format_cpf(obj.cnpj_cpf)

    def has_delete_permission(self, request, obj=None):
        return False
        return obj.cnpj_cpf

    def get_urls(self):
        urls = filter(dashboard.valid_url, super().get_urls())
        return list(urls)
    def supplier_info(self, obj):
        return '{}<br>{}'.format(obj.supplier, self._format_document(obj))

    supplier_info.short_description = 'Fornecedor'
    supplier_info.allow_tags = True

    def jarbas(self, obj):
        base_url = 'https://jarbas.serenatadeamor.org/#/documentId/{}/'
        url = base_url.format(obj.document_id)
        image_src = '/static/favicon/favicon-16x16.png'
        image = '<img alt="View on Jarbas" src="{}">'.format(image_src)
        return '<a href="{}">{}</a>'.format(url, image)

    jarbas.short_description = ''
    jarbas.allow_tags = True

    def is_suspicious(self, obj):
        return obj.suspicions is not None

    is_suspicious.short_description = 'Suspicious'
    is_suspicious.boolean = True

    def value(self, obj):
        return 'R$ {:.2f}'.format(obj.total_net_value)#replace('.', ',')

    value.short_description = 'valor'

    def still_available(self, obj):
        return obj.available_in_latest_dataset

    still_available.short_description = 'disponível na Câmara'
    still_available.boolean = True

    def short_document_id(self, obj):
        return obj.document_id

    short_document_id.short_description = 'Reembolso'


dashboard.register(Reimbursement, ReimbursementModelAdmin)
