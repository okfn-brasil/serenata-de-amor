from django.test import TestCase
from webassets.bundle import get_all_bundle_files

from jarbas.frontend.assets import elm


class TestDependencies(TestCase):

    def test_dependencies(self):
        files = set(get_all_bundle_files(elm))
        self.assertEqual(9, len(files), files)
