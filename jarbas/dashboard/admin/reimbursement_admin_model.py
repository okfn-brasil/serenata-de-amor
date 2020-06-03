
from brazilnum.cnpj import format_cnpj
from brazilnum.cpf import format_cpf
from django.utils.safestring import mark_safe

from jarbas.public_admin.admin import PublicAdminModelAdmin


class ReimbursementAdmin(PublicAdminModelAdmin):

    def short_document_id(self, obj):
        return obj.document_id

    short_document_id.short_description = 'Reembolso'

    def suspicious(self, obj):
        return obj.suspicions is not None

    suspicious.short_description = 'suspeito'
    suspicious.boolean = True

    def supplier_info(self, obj):
        return mark_safe(f'{obj.supplier}<br>{self._format_document(obj)}')

    supplier_info.short_description = 'Fornecedor'

    def _format_document(self, obj):
        if obj.cnpj_cpf:
            if len(obj.cnpj_cpf) == 14:
                return format_cnpj(obj.cnpj_cpf)

            if len(obj.cnpj_cpf) == 11:
                return format_cpf(obj.cnpj_cpf)

            return obj.cnpj_cpf

    def _format_currency(self, value):
        return 'R$ {:.2f}'.format(value).replace('.', ',')
