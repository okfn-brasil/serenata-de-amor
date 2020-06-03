from jarbas.dashboard.admin.reimbursement_admin_model import ReimbursementAdmin


class FederalSenateReimbursementModelAdmin(ReimbursementAdmin):
    list_display = (
        'short_document_id',
        'congressperson_name',
        'year',
        'expense_type',
        'supplier_info',
        'value',
        'suspicious',
    )

    def value(self, obj):
        return self._format_currency(obj.reimbursement_value)

    value.short_description = 'valor'
