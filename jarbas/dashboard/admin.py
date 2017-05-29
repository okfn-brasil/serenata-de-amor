from django.contrib import admin
from jarbas.core.models import Reimbursement


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

    def is_suspicious(self, obj):
        return obj.suspicions is not None

    is_suspicious.short_description = 'Suspicious'
    is_suspicious.boolean = True


admin.site.site_title = 'Dashboard'
admin.site.site_header = 'Jarbas Dashboard'
admin.site.index_title = 'Jarbas'
admin.site.register(Reimbursement, ReimbursementModelAdmin)
