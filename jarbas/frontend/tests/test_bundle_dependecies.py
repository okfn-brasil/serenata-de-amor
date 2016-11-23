from glob import glob
from django.test import TestCase
from webassets.bundle import get_all_bundle_files

from jarbas.frontend.assets import elm


class TestDependencies(TestCase):

    def test_dependencies(self):
        expected = len(glob('jarbas/frontend/elm/**/*.elm', recursive=True))
        files = set(get_all_bundle_files(elm))
        self.assertEqual(expected, len(files), files)
