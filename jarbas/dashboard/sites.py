from django.contrib.admin.sites import AdminSite


class DashboardSite(AdminSite):

    site_title = 'Dashboard'
    site_header = 'Jarbas Dashboard'
    index_title = 'Jarbas'

    def __init__(self):
        super().__init__('dashboard')
        self._actions, self._global_actions = {}, {}

    @staticmethod
    def _valid_url(url):
        for label in ('auth', 'login', 'logout', 'password'):
            if label in url.regex.pattern:
                return False
        return True

    @property
    def urls(self):
        urls = filter(self._valid_url, self.get_urls())
        return list(urls), 'admin', self.name

dashboard = DashboardSite()
