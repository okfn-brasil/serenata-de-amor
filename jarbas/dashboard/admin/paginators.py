from hashlib import md5

from django.core.cache import cache
from django.core.paginator import Paginator


class CachedCountPaginator(Paginator):
    """Cached the paginator count (for performance)"""

    @property
    def count(self):
        query = self.object_list.query.__str__()
        hashed = md5(query.encode('utf-8')).hexdigest()
        key = f'dashboard_count_{hashed}'
        count = cache.get(key)

        if count is None:
            count = super(CachedCountPaginator, self).count
            cache.set(key, count, 60 * 60 * 6)

        return count
