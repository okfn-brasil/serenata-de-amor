import os

import numpy as np
import pandas as pd
from serenata_toolbox.federal_senate.federal_senate_dataset import FederalSenateDataset
from serenata_toolbox.datasets import fetch

COLUMNS = {
    'net_value': 'total_net_value',
    'recipient_id': 'cnpj_cpf',
    'recipient': 'supplier',
}

class Adapter:
    def __init__(self, path):
        self.path = path

    @property
    def dataset(self):
        self.update_datasets()
        self.prepare_dataset()

    def update_datasets(self):
        os.makedirs(self.path, exist_ok=True)
        federal_senate = FederalSenateDataset(self.path)
        federal_senate.fetch()
        federal_senate.translate()
        federal_senate.clean()

