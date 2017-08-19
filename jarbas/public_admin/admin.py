import re

from simple_history.admin import SimpleHistoryAdmin

from jarbas.public_admin.sites import public_admin


class PublicAdminModelAdmin(SimpleHistoryAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method == 'GET'

    def has_delete_permission(self, request, obj=None):
        return False

    @staticmethod
    def rename_change_url(url):
        if 'change' in url.regex.pattern:
            new_re = url.regex.pattern.replace('change', 'details')
            url.regex = re.compile(new_re, re.UNICODE)
        return url

    def get_urls(self):
        return [
            self.rename_change_url(url) for url in super().get_urls()
            if public_admin.valid_url(url)
        ]
