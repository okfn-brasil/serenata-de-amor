import shutil
import os
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import patch
from shutil import copy2

import pandas as pd

from rosie.federal_senate.adapter import Adapter as subject_class
from rosie.federal_senate.adapter import COLUMNS as ADAPTER_COLUMNS

class TestAdapter(TestCase):
    def setUp(self):
        self.temp_path = mkdtemp()
        self.fixtures_path = os.path.join('rosie', 'federal_senate', 'tests', 'fixtures')
        copies = (
            ('reimbursements.xz', 'reimbursements.xz')
        )
        for source, target in copies:
            copy2(os.path.join(self.fixtures_path, source), os.path.join(self.temp_path, target))
        self.subject = subject_class(self.temp_path)

    def tearDown(self):
        shutil.rmtree(self.temp_path)
