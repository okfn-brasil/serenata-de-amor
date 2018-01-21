import os

from webassets.version import Manifest

try:
    from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

    class DjangoManifest(Manifest):
        """Stores version data in Django's ManifestStaticFileStorage.
        """

        id = 'django'

        def __init__(self, *a, **kw):
            try:
                import json
            except ImportError:
                import simplejson as json
            self.json = json
            self.storage = ManifestStaticFilesStorage()
            self._load_manifest()

        def remember(self, bundle, ctx, version):
            output_filename = bundle.resolve_output(ctx, version=version)
            output_filename = os.path.relpath(output_filename, ctx.directory)
            source_filename = self.name_without_hash(bundle.output)

            self.storage.hashed_files[source_filename] = output_filename
            self._save_manifest()

        def query(self, bundle, ctx):
            if ctx.auto_build:
                self._load_manifest()

            source_filename = self.name_without_hash(bundle.output)
            output = self.storage.hashed_files.get(source_filename, None)
            if output:
                # foo.hash.js
                name_with_hash, ext = os.path.splitext(output)
                output = os.path.splitext(name_with_hash)[1]

            return output

        def name_without_hash(self, filename):
            name_with_hash, ext = os.path.splitext(filename)
            name = os.path.splitext(name_with_hash)[0]
            return name + ext

        def _load_manifest(self):
            self.storage.load_manifest()

        def _save_manifest(self):
            self.storage.save_manifest()

except ImportError:
    class DjangoManifest(object):
        pass
