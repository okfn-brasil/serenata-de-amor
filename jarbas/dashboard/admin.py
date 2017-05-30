from django.contrib import admin

from jarbas.core.models import Reimbursement
from jarbas.dashboard.sites import dashboard


class SuspiciousListFilter(admin.SimpleListFilter):

    title = 'Is suspicious'

    parameter_name = 'is_suspicions'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no',  'No'),
        )

    def queryset(self, request, queryset):
        return queryset.suspicions() if self.value() == 'yes' else queryset


class ReimbursementModelAdmin(admin.ModelAdmin):

    list_display = (
        'document_id',
        'jarbas',
        'congressperson_name',
        'year',
        'subquota_description',
        'supplier',
        'cnpj_cpf',
        'is_suspicious',
        'total_net_value',
        'available_in_latest_dataset',
    )
    search_fields = (
        'applicant_id',
        'cnpj_cpf',
        'congressperson_name',
        'document_id',
        'party',
        'state',
        'supplier',
    )
    list_filter = (
        SuspiciousListFilter,
        'available_in_latest_dataset',
        'year',
        'state',
    )
    readonly_fields = tuple(f.name for f in Reimbursement._meta.fields)
    has_permission = dashboard.has_permission

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = filter(dashboard.valid_url, super().get_urls())
        return list(urls)

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


dashboard.register(Reimbursement, ReimbursementModelAdmin)
