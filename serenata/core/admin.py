from django.contrib import admin

from serenata.core.models import Document


class DocumentModelAdmin(admin.ModelAdmin):
    pass

admin.site.register(Document, DocumentModelAdmin)
