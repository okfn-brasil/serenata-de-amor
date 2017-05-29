from functools import update_wrapper

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.utils.crypto import get_random_string
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from jarbas.core.models import Reimbursement


class DashboardSite(AdminSite):

    site_title = 'Dashboard'
    site_header = 'Jarbas Dashboard'
    index_title = 'Jarbas'

    def __init__(self):
        super().__init__('dashboard')
        self._actions, self._global_actions = {}, {}

    @staticmethod
    def get_user():
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username='dashboard')
        except user_model.DoesNotExist:
            user_kwargs = dict(password=get_random_string(128), is_staff=True)
            user = user_model.objects.create_user('dashboard', **user_kwargs)
            permission = Permission.objects.get(
                content_type=ContentType.objects.get_for_model(Reimbursement),
                codename='change_reimbursement'
            )
            user.user_permissions.add(permission)
            user = user_model.objects.get(username='dashboard')  # avoid cache
        return user

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
        for label in forbidden:
            if label in url.regex.pattern:
                return False
        return True

    @property
    def urls(self):
        urls = filter(self.valid_url, self.get_urls())
        return list(urls), 'admin', self.name

    def has_permission(self, request):
        if request.method != 'GET':
            return False

        request.user = self.get_user()
        return super().has_permission(request)

    def admin_view(self, view, cacheable=False):
        def inner(request, *args, **kwargs):
            request.user = self.get_user()
            if not self.has_permission(request):
                return HttpResponseForbidden()
            return view(request, *args, **kwargs)

        if not cacheable:
            inner = never_cache(inner)

        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)

        return update_wrapper(inner, view)


dashboard = DashboardSite()
