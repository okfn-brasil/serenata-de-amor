from django.conf import settings
from django.contrib import staticfiles
from django.core.files.storage import FileSystemStorage
from django_assets.env import get_env
from webassets.exceptions import BundleError

from django.contrib.staticfiles.utils import matches_patterns


class AssetsFileStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        super(AssetsFileStorage, self).__init__(
            location or get_env().directory,
            base_url or get_env().url,
            *args, **kwargs)


class AssetsFinder(staticfiles.finders.BaseStorageFinder):
    """A staticfiles finder that will serve from ASSETS_ROOT (which
    defaults to STATIC_ROOT).

    This is required when using the django.contrib.staticfiles app
    in development, because the Django devserver will not serve files
    from STATIC_ROOT (or ASSETS_ROOT) by default - which is were the
    merged assets are written.
    """

    # Make this finder search ``Environment.directory``.
    storage = AssetsFileStorage

    def list(self, ignore_patterns):
        # While ``StaticFileStorage`` itself is smart enough not to stumble
        # over this finder returning the full contents of STATIC_ROOT via
        # ``AssetsFileStorage``, ``CachedAssetsFileStorage`` is not. It would
        # create hashed versions of already hashed files.
        #
        # Since the development ``serve`` view will not use this ``list()``
        # method, but the ``collectstatic`` command does, we can customize
        # it to deal with ``CachedAssetsFileStorage``.
        #
        # We restrict the files returned to known bundle output files. Those
        # will then be post-processed by ``CachedAssetsFileStorage`` and
        # properly hashed and rewritten.
        #
        # See also this discussion:
        #    https://github.com/miracle2k/webassets/issues/114

        env = get_env()
        if env.directory == getattr(settings, 'STATIC_ROOT'):
            for bundle in env:
                try:
                    output = bundle.resolve_output(env)
                except BundleError:
                    # We don't have a version for this bundle
                    continue

                if not matches_patterns(output, ignore_patterns) and \
                 self.storage.exists(output):
                    yield output, self.storage
        else:
            # When ASSETS_ROOT is a separate directory independent of
            # STATIC_ROOT, we're good just letting all files be collected.
            for output in super(AssetsFinder, self).list(ignore_patterns):
                yield output
