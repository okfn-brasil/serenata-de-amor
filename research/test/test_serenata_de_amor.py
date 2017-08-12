import glob
from unittest import TestCase


class TestSerenataDeAmor(TestCase):

    def setUp(self):
        self.notebook_files = glob.glob('develop/*.ipynb')

    def test_html_versions_present(self):
        """There is a *.html version of every Jupyter notebook."""
        expected = [filename.replace('.ipynb', '.html')
                    for filename in self.notebook_files]
        html_files = glob.glob('develop/*.html')
        self.assertEqual(expected, html_files)

    def test_py_versions_present(self):
        """There is a *.py version of every Jupyter notebook."""
        expected = [filename.replace('.ipynb', '.py')
                    for filename in self.notebook_files]
        py_files = glob.glob('develop/*.py')
        self.assertEqual(expected, py_files)
