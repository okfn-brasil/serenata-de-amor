from decimal import Decimal
from hashlib import md5

from brazilnum.cnpj import format_cnpj
from brazilnum.cpf import format_cpf
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.cache import cache
from django.db.models import Count, F, Max, Min, Sum
from django.db.models.functions import Concat
from django.utils.safestring import mark_safe

from jarbas.chamber_of_deputies.models import (
    Reimbursement,
    ReimbursementSummary
)
from jarbas.chamber_of_deputies.serializers import clean_cnpj_cpf
from jarbas.dashboard.admin import list_filters, widgets
from jarbas.dashboard.admin.paginators import CachedCountPaginator
from jarbas.dashboard.admin.subquotas import Subquotas
from jarbas.public_admin.admin import PublicAdminModelAdmin
from jarbas.public_admin.sites import public_admin


ALL_FIELDS = sorted(Reimbursement._meta.fields, key=lambda f: f.verbose_name)
CUSTOM_WIDGETS = ('receipt_url', 'subquota_description', 'suspicions')
READONLY_FIELDS = (f.name for f in ALL_FIELDS if f.name not in CUSTOM_WIDGETS)


class ReimbursementModelAdmin(PublicAdminModelAdmin):

    list_display = (
        'short_document_id',
        'jarbas',
        'rosies_tweet',
        'receipt_link',
        'congressperson_name',
        'year',
        'subquota_translated',
        'supplier_info',
        'value',
        'suspicious'
    )

    search_fields = ('search_vector',)

    list_filter = (
        list_filters.SuspiciousListFilter,
        list_filters.HasReceiptFilter,
        list_filters.HasReimbursementNumberFilter,
        list_filters.StateListFilter,
        list_filters.YearListFilter,
        list_filters.MonthListFilter,
        list_filters.DocumentTypeListFilter,
        list_filters.SubquotaListFilter,
    )

    fields = tuple(f.name for f in ALL_FIELDS)
    readonly_fields = tuple(READONLY_FIELDS)
    list_select_related = ('tweet',)
    paginator = CachedCountPaginator

    def _format_document(self, obj):
        if obj.cnpj_cpf:
            if len(obj.cnpj_cpf) == 14:
                return format_cnpj(obj.cnpj_cpf)

            if len(obj.cnpj_cpf) == 11:
                return format_cpf(obj.cnpj_cpf)

            return obj.cnpj_cpf

    def supplier_info(self, obj):
        return mark_safe(f'{obj.supplier}<br>{self._format_document(obj)}')

    supplier_info.short_description = 'Fornecedor'

    def jarbas(self, obj):
        base_url = '/layers/#/documentId/{}/'
        url = base_url.format(obj.document_id)
        image_src = '/static/favicon/favicon-16x16.png'
        image = '<img alt="Ver no Jarbas" src="{}">'.format(image_src)
        return mark_safe('<a href="{}">{}</a>'.format(url, image))

    jarbas.short_description = ''

    def rosies_tweet(self, obj):
        try:
            return mark_safe('<a href="{}">🤖</a>'.format(obj.tweet.get_url()))
        except Reimbursement.tweet.RelatedObjectDoesNotExist:
            return ''

    rosies_tweet.short_description = ''

    def receipt_link(self, obj):
        if not obj.receipt_url:
            return ''
        return mark_safe(f'<a target="_blank" href="{obj.receipt_url}">📃</a>')

    receipt_link.short_description = ''

    def suspicious(self, obj):
        return obj.suspicions is not None

    suspicious.short_description = 'suspeito'
    suspicious.boolean = True

    def has_receipt_url(self, obj):
        return obj.receipt_url is not None

    has_receipt_url.short_description = 'recibo'
    has_receipt_url.boolean = True

    def value(self, obj):
        return 'R$ {:.2f}'.format(obj.total_net_value).replace('.', ',')

    value.short_description = 'valor'
    value.admin_order_field = 'total_net_value'

    def short_document_id(self, obj):
        return obj.document_id

    short_document_id.short_description = 'Reembolso'

    def subquota_translated(self, obj):
        return Subquotas.pt_br(obj.subquota_description)

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj and not obj.receipt_fetched:
            obj.get_receipt_url()
        return obj

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in CUSTOM_WIDGETS:
            custom_widgets = dict(
                subquota_description=widgets.SubquotaWidget,
                receipt_url=widgets.ReceiptUrlWidget,
                suspicions=widgets.SuspiciousWidget
            )
            kwargs['widget'] = custom_widgets.get(db_field.name)
        return super().formfield_for_dbfield(db_field, **kwargs)

    def get_search_results(self, request, queryset, search_term):
        queryset, distinct = super(ReimbursementModelAdmin, self) \
            .get_search_results(request, queryset, None)

        if search_term:
            # if a cnpj/cpf strip characters other than digits
            search_term = clean_cnpj_cpf(search_term)
            query = SearchQuery(search_term, config='portuguese')
            rank = SearchRank(F('search_vector'), query)
            queryset = queryset.annotate(rank=rank).filter(search_vector=query)

            if not queryset.was_ordered():
                queryset.order_by('-rank')

        return queryset, distinct


class ReimbursementSummaryModelAdmin(PublicAdminModelAdmin):
    change_list_template = 'dashboard/reimbursement_summary_change_list.html'
    list_filter = (
        list_filters.SuspiciousListFilter,
        list_filters.HasReimbursementNumberFilter,
        list_filters.StateListFilter,
        list_filters.YearListFilter,
        list_filters.MonthListFilter,
        list_filters.DocumentTypeListFilter,
    )

    def get_period(self, request):
        if 'year' in request.GET:
            return 'month'
        return 'year'

    @staticmethod
    def bar_chart_height(row, low, high):
        total, low, high = row['total'] or 0, low or 0, high or 0
        if low == high:
            size = 0
        else:
            size = (total - low) / (high - low) * 100

        corrected_size = Decimal('5') + (Decimal('0.95') * size)
        return corrected_size

    def get_cached_context(self, request, queryset):
        url = request.build_absolute_uri()
        hashed = md5(url.encode('utf-8')).hexdigest()
        key = f'cached_reimbursement_summary_context_{hashed}'
        context = cache.get(key)

        if context is not None:
            return context

        metrics = {
            'total_reimbursements': Count('id'),
            'total_value': Sum('total_net_value'),
        }
        queryset = (
            queryset
            .values('subquota_description')
            .annotate(**metrics)
            .order_by('-total_value')
        )

        period = self.get_period(request)
        if period == 'year':
            period_key = 'year'
            summary_over_time = (
                queryset
                .values('year')
                .annotate(total=Sum('total_net_value'))
                .order_by('year')
            )
        else:
            period_key = 'period'
            summary_over_time = (
                queryset
                .annotate(period=Concat('year', 'month'))
                .values('period')
                .annotate(total=Sum('total_net_value'))
                .order_by('year', 'month')
            )

        summary_range = summary_over_time.aggregate(
            low=Min('total'),
            high=Max('total')
        )
        high = summary_range.get('high', 0)
        low = summary_range.get('low', 0)

        context = {
            'period': period,
            'summary': tuple(queryset),
            'summary_total': dict(queryset.aggregate(**metrics)),
            'summary_over_time': tuple({
                'label': period,
                'period': row[period_key],
                'total': row['total'] or 0,
                'percent': self.bar_chart_height(row, low, high)
            } for row in summary_over_time)
        }

        cache.set(key, context, 60 * 60 * 6)
        return context

    def changelist_view(self, request, extra=None):
        response = super().changelist_view(request, extra_context=extra)

        try:
            queryset = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        context = self.get_cached_context(request, queryset)
        response.context_data.update(context)
        return response


public_admin.register(Reimbursement, ReimbursementModelAdmin)
public_admin.register(ReimbursementSummary, ReimbursementSummaryModelAdmin)
