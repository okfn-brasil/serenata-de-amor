from decimal import Decimal, InvalidOperation
from hashlib import md5

from brazilnum.cnpj import format_cnpj
from brazilnum.cpf import format_cpf
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.cache import cache
from django.db.models import Count, F, Sum
from django.db.models.functions import Concat
from django.utils.safestring import mark_safe

from jarbas.chamber_of_deputies.models import (
    Reimbursement,
    ReimbursementSummary,
    SocialMedia,
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
        'social_profile',
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
        image = '<img alt="Ver no Jarbas" src="/static/favicon/favicon-16x16.png">'
        return mark_safe('<a href="{}">{}</a>'.format(url, image))

    jarbas.short_description = ''

    def social_profile(self, obj):
        social_media = SocialMedia.objects.filter(congressperson_id=obj.congressperson_id).first()
        if not social_media:
            return ''

        tw_link = ''
        tw_img = '/static/image/twitter-icon.png'
        tw_profile = social_media.twitter_profile or social_media.secondary_twitter_profile
        if tw_profile:
            tw_link = '<a href="http://twitter.com/{}"><img src="{}" width="16"></a>'.format(
                tw_profile, tw_img
            )

        fb_link = ''
        fb_img = '/static/image/facebook-icon.png'
        if social_media.facebook_page:
            fb_link = '<a href="{}"><img src="{}" width="16"></a>'.format(
                social_media.facebook_page, fb_img
            )

        return mark_safe(f'{tw_link} {fb_link}')

    social_profile.short_description = 'Social'

    def rosies_tweet(self, obj):
        try:
            return mark_safe('<a href="{}">🤖</a>'.format(obj.tweet.get_url()))
        except Reimbursement.tweet.RelatedObjectDoesNotExist:
            return ''

    rosies_tweet.short_description = ''

    def receipt_link(self, obj):
        if not obj.receipt_url:
            return ''
        image = '<img src="/static/image/receipt_icon.png">'
        return mark_safe('<a target="_blank" href="{}">{}</a>'.format(obj.receipt_url, image))

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

    def get_chart_grouping(self, request):
        """Depending on the year selected on the sidebar filters, returns the
        grouping criteria for the bottom bar chart:
        * if user is seeing a page with no year filter, the chart shows
        reimbursements grouped by year
        * if the user is seeing a page filtered by a specific year, the chart
        shows reimbursements grouped by month
        """
        if 'year' in request.GET:
            return 'month'
        return 'year'

    @staticmethod
    def serialize_summary_over_time(row, minimum_percentage='0.05', **kwargs):
        low = kwargs.get('low') or Decimal('0')
        high = kwargs.get('high') or Decimal('0')
        chart_grouping = kwargs.get('chart_grouping')
        chart_grouping_key = kwargs.get('chart_grouping_key')
        minimum_percentage = Decimal(minimum_percentage)
        total = row['total']

        try:
            percentage = (total - low) / (high - low)
        except InvalidOperation:
            percentage = Decimal('0')

        ratio = Decimal('1') - minimum_percentage
        corrected_percentage = minimum_percentage + (ratio * percentage)
        bar_height = Decimal('100') * corrected_percentage

        return {
            'label': chart_grouping,
            'chart_grouping': row[chart_grouping_key],
            'total': row['total'] or 0,
            'percent': bar_height
        }

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

        chart_grouping = self.get_chart_grouping(request)
        if chart_grouping == 'year':
            chart_grouping_key = 'year'
            summary_over_time = (
                queryset
                .values('year')
                .annotate(total=Sum('total_net_value'))
                .order_by('year')
            )
        else:
            chart_grouping_key = 'chart_grouping'
            summary_over_time = (
                queryset
                .annotate(chart_grouping=Concat('year', 'month'))
                .values('chart_grouping')
                .annotate(total=Sum('total_net_value'))
                .order_by('year', 'month')
            )

        summary_over_time = tuple(summary_over_time)
        totals = tuple(row['total'] for row in summary_over_time)
        over_time_args = {
            'chart_grouping': chart_grouping,
            'chart_grouping_key': chart_grouping_key,
            'low': min(totals, default=0),
            'high': max(totals, default=0)
        }

        context = {
            'year': request.GET.get('year'),
            'month': request.GET.get('month'),
            'chart_grouping': chart_grouping,
            'summary': tuple(queryset),
            'summary_total': dict(queryset.aggregate(**metrics)),
            'summary_over_time': tuple(
                self.serialize_summary_over_time(row, **over_time_args)
                for row in summary_over_time
            )
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
