import json
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


class SuspiciousWidget(Widget):

    SUSPICIONS = (
        'meal_price_outlier',
        'over_monthly_subquota_limit',
        'suspicious_traveled_speed_day',
        'invalid_cnpj_cpf',
        'election_expenses',
        'irregular_companies_classifier'
    )

    HUMAN_NAMES = (
        'Preço de refeição muito incomum',
        'Extrapolou limita da (sub)quota',
        'Muitas despesas em diferentes cidades no mesmo dia',
        'CPF ou CNPJ inválidos',
        'Gasto com campanha eleitoral',
        'CNPJ irregular'
    )

    MAP = dict(zip(SUSPICIONS, HUMAN_NAMES))

    def render(self, name, value, attrs=None, renderer=None):
        value_as_dict = json.loads(value)
        if not value_as_dict:
            return ''

        values = (self.MAP.get(k, k) for k in value_as_dict.keys())
        suspicions = '<br>'.join(values)
        return '<div class="readonly">{}</div>'.format(suspicions)


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


class Subquotas:

    EN_US = (
        'Maintenance of office supporting parliamentary activity',
        'Locomotion, meal and lodging',
        'Fuels and lubricants',
        'Consultancy, research and technical work',
        'Publicity of parliamentary activity',
        'Purchase of office supplies',
        'Software purchase or renting; Postal services; Subscriptions',
        'Security service provided by specialized company',
        'Flight tickets',
        'Telecommunication',
        'Postal services',
        'Publication subscriptions',
        'Congressperson meal',
        'Lodging, except for congressperson from Distrito Federal',
        'Automotive vehicle renting or watercraft charter',
        'Aircraft renting or charter of aircraft',
        'Automotive vehicle renting or charter',
        'Watercraft renting or charter',
        'Taxi, toll and parking',
        'Terrestrial, maritime and fluvial tickets',
        'Participation in course, talk or similar event',
        'Flight ticket issue'
    )

    PT_BR = (
        'Manutenção de escritório de apoio à atividade parlamentar',
        'Locomoção, alimentação e  hospedagem',
        'Combustíveis e lubrificantes',
        'Consultorias, pesquisas e trabalhos técnicos',
        'Divulgação da atividade parlamentar',
        'Aquisição de material de escritório',
        'Aquisição ou loc. de software serv. postais ass.',
        'Serviço de segurança prestado por empresa especializada',
        'Passagens aéreas',
        'Telefonia',
        'Serviços postais',
        'Assinatura de publicações',
        'Fornecimento de alimentação do parlamentar',
        'Hospedagem ,exceto do parlamentar no distrito federal',
        'Locação de veículos automotores ou fretamento de embarcações',
        'Locação ou fretamento de aeronaves',
        'Locação ou fretamento de veículos automotores',
        'Locação ou fretamento de embarcações',
        'Serviço de táxi, pedágio e estacionamento',
        'Passagens terrestres, marítimas ou fluviais',
        'Participação em curso, palestra ou evento similar',
        'Emissão bilhete aéreo'
    )

    NUMBERS = (
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        119,
        120,
        121,
        122,
        123,
        137,
        999
    )

    OPTIONS = sorted(zip(NUMBERS, PT_BR), key=lambda t: t[1])

    @classmethod
    def pt_br(cls, en_us):
        translations = dict(zip(cls.EN_US, cls.PT_BR))
        return translations.get(en_us)

    def en_us(cls, pt_br):
        translations = dict(zip(cls.PT_BR, cls.EN_US))
        return translations.get(pt_br)

class SubquotaWidget(Widget, Subquotas):

    def render(self, name, value, attrs=None, renderer=None):
        value = self.pt_br(value) or value
        return '<div class="readonly">{}</div>'.format(value)


class SubquotaListFilter(SimpleListFilter, Subquotas):

    title = 'subcota'
    parameter_name = 'subquota_id'
    default_value = None

    def lookups(self, request, model_admin):
        return self.OPTIONS

    def value(self):
        try:
            return int(super().value())
        except (TypeError, ValueError):
            return None

    def queryset(self, request, queryset):
        subquota = dict(self.OPTIONS).get(self.value())
        if not subquota:
            return queryset
        return queryset.filter(subquota_description=self.en_us(subquota))


class ReimbursementModelAdmin(SimpleHistoryAdmin):

    list_display = (
        'short_document_id',
        'jarbas',
        'congressperson_name',
        'year',
        'subquota_translated',
        'supplier_info',
        'value',
        'suspicious',
        # 'still_available',
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
        # 'available_in_latest_dataset',
        'state',
        'year',
        SubquotaListFilter,
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
    value.admin_order_field = 'total_net_value'

    def still_available(self, obj):
        return obj.available_in_latest_dataset

    still_available.short_description = 'disponível na Câmara'
    still_available.boolean = True

    def short_document_id(self, obj):
        return obj.document_id

    short_document_id.short_description = 'Reembolso'

    def subquota_translated(self, obj):
        return Subquotas.pt_br(obj.subquota_description)

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

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj and not obj.receipt_fetched:
            obj.get_receipt_url()
        return obj

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in CUSTOM_WIDGETS:
            widgets = dict(
                subquota_description=SubquotaWidget,
                receipt_url=ReceiptUrlWidget,
                suspicions=SuspiciousWidget
            )
            kwargs['widget'] = widgets.get(db_field.name)
        return super().formfield_for_dbfield(db_field, **kwargs)


dashboard.register(Reimbursement, ReimbursementModelAdmin)
