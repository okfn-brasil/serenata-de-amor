import re

from brazilnum.cnpj import format_cnpj
from brazilnum.cpf import format_cpf
from django.contrib.admin import SimpleListFilter
from django.forms.widgets import Widget
from simple_history.admin import SimpleHistoryAdmin

from jarbas.core.models import Reimbursement
from jarbas.dashboard.sites import dashboard


ALL_FIELDS = sorted(Reimbursement._meta.fields, key=lambda f: f.verbose_name)
CUSTOM_WIDGETS = ('receipt_url', 'subquota_description', 'suspicions')
READONLY_FIELDS = (f.name for f in ALL_FIELDS if f.name not in CUSTOM_WIDGETS)


class ReceiptUrlWidget(Widget):

    def render(self, name, value, attrs=None, renderer=None):
        if not value:
            return ''

        url = '<div class="readonly"><a href="{}" target="_blank">{}</a></div>'
        return url.format(value, value)
class SuspiciousListFilter(SimpleListFilter):

    title = 'reembolso suspeito'
    parameter_name = 'is_suspicions'
    options = (
        ('yes', 'Sim'),
        ('no', 'Não'),
    )

    def lookups(self, request, model_admin):
        return self.options

    def queryset(self, request, queryset):
        return queryset.suspicions() if self.value() == 'yes' else queryset


class SubuotaListfilter(SimpleListFilter):

    title = 'subquota'
    parameter_name = 'subquota_id'
    options = (
        (1, 'Manutenção de escritório de apoio à atividade parlamentar'),
        (2, 'Locomoção, alimentação e  hospedagem'),
        (3, 'Combustíveis e lubrificantes'),
        (4, 'Consultorias, pesquisas e trabalhos técnicos'),
        (5, 'Divulgação da atividade parlamentar'),
        (6, 'Aquisição de material de escritório'),
        (7, 'Aquisição ou loc. de software serv. postais ass.'),
        (8, 'Serviço de segurança prestado por empresa especializada'),
        (9, 'Passagens aéreas'),
        (10, 'Telefonia'),
        (11, 'Serviços postais'),
        (12, 'Assinatura de publicações'),
        (13, 'Fornecimento de alimentação do parlamentar'),
        (14, 'Hospedagem ,exceto do parlamentar no distrito federal'),
        (15, 'Locação de veículos automotores ou fretamento de embarcações'),
        (119, 'Locação ou fretamento de aeronaves'),
        (120, 'Locação ou fretamento de veículos automotores'),
        (121, 'Locação ou fretamento de embarcações'),
        (122, 'Serviço de táxi, pedágio e estacionamento'),
        (123, 'Passagens terrestres, marítimas ou fluviais'),
        (137, 'Participação em curso, palestra ou evento similar'),
        (999, 'Emissão Bilhete Aéreo')
    )

    def lookups(self, request, model_admin):
        return self.options

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(subquota_id=self.value())


class ReimbursementModelAdmin(SimpleHistoryAdmin):

    list_display = (
        'short_document_id',
        'jarbas',
        'congressperson_name',
        'year',
        'subquota_description',
        'supplier_info',
        'value',
        'suspicious',
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
        SubuotaListfilter,
    )

    fields = tuple(f.name for f in ALL_FIELDS)
    readonly_fields = tuple(READONLY_FIELDS)

    def _format_document(self, obj):
        if obj.cnpj_cpf:
            if len(obj.cnpj_cpf) == 14:
                return format_cnpj(obj.cnpj_cpf)

            if len(obj.cnpj_cpf) == 11:
                return format_cpf(obj.cnpj_cpf)

            return obj.cnpj_cpf

    def supplier_info(self, obj):
        return '{}<br>{}'.format(obj.supplier, self._format_document(obj))

    supplier_info.short_description = 'Fornecedor'
    supplier_info.allow_tags = True

    def jarbas(self, obj):
        base_url = 'https://jarbas.serenatadeamor.org/#/documentId/{}/'
        url = base_url.format(obj.document_id)
        image_src = '/static/favicon/favicon-16x16.png'
        image = '<img alt="Ver no Jarbas" src="{}">'.format(image_src)
        return '<a href="{}">{}</a>'.format(url, image)

    jarbas.short_description = ''
    jarbas.allow_tags = True

    def suspicious(self, obj):
        return obj.suspicions is not None

    suspicious.short_description = 'suspeito'
    suspicious.boolean = True

    def value(self, obj):
        return 'R$ {:.2f}'.format(obj.total_net_value).replace('.', ',')

    value.short_description = 'valor'

    def still_available(self, obj):
        return obj.available_in_latest_dataset

    still_available.short_description = 'disponível na Câmara'
    still_available.boolean = True

    def short_document_id(self, obj):
        return obj.document_id

    short_document_id.short_description = 'Reembolso'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if request.method != 'GET':
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    @staticmethod
    def rename_change_url(url):
        if 'change' in url.regex.pattern:
            new_re = url.regex.pattern.replace('change', 'details')
            url.regex = re.compile(new_re, re.UNICODE)
        return url

    def get_urls(self):
        urls = filter(dashboard.valid_url, super().get_urls())
        return list(map(self.rename_change_url, urls))

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in CUSTOM_WIDGETS:
            widgets = dict(
                receipt_url=ReceiptUrlWidget,
            )
            kwargs['widget'] = widgets.get(db_field.name)
        return super().formfield_for_dbfield(db_field, **kwargs)


dashboard.register(Reimbursement, ReimbursementModelAdmin)
