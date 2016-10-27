import os
from glob import glob

from django.conf import settings
from django_assets import Bundle, register
from webassets.filter import register_filter
from webassets_elm import Elm

register_filter(Elm)

frontend_path = os.path.dirname(settings.ASSETS_ROOT)
depends = glob(os.path.join(frontend_path, 'elm', '**', '*.elm'), recursive=True)

elm = Bundle(
    os.path.join(frontend_path, 'elm', 'Main.elm'),
    filters=('elm', 'rjsmin'),
    depends=depends,
    output='app.js'
)

register('elm', elm)
