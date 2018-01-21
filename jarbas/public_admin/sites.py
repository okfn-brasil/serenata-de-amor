from functools import update_wrapper

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_protect


class DummyUser(AnonymousUser):
    def has_module_perms(self, app_label):
        return app_label == 'chamber_of_deputies'

    def has_perm(self, permission, obj=None):
        return permission == 'chamber_of_deputies.change_reimbursement'


class PublicAdminSite(AdminSite):

    site_title = 'Dashboard'
    site_header = 'Jarbas Dashboard'
    index_title = 'Jarbas'

    def __init__(self):
        super().__init__('dashboard')
        self._actions, self._global_actions = {}, {}

    @staticmethod
    def valid_url(url):
        forbidden = (
            'auth',
            'login',
            'logout',
            'password',
            'add',
            'delete',
        )
        return all(
            label not in url.pattern.regex.pattern for label in forbidden)

    @property
    def urls(self):
        urls = (url for url in self.get_urls() if self.valid_url(url))
        return list(urls), 'admin', self.name

    def has_permission(self, request):
        return request.method == 'GET'

    def admin_view(self, view, cacheable=False):
        def inner(request, *args, **kwargs):
            request.user = DummyUser()
            if not self.has_permission(request):
                return HttpResponseForbidden()
            return view(request, *args, **kwargs)

        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)

        return update_wrapper(inner, view)


public_admin = PublicAdminSite()
