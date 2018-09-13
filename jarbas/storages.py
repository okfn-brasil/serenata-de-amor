from whitenoise.storage import CompressedManifestStaticFilesStorage


class WhiteNoiseStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False

    def hashed_name(self, *args, **kwargs):
        """Skip hashing app.js because it is included in the container volume
        after collectstatic runs."""
        name, *_ = args
        if name.endswith('/static/app.js'):
            return name

        name = super(WhiteNoiseStaticFilesStorage, self).hashed_name(*args, **kwargs)
