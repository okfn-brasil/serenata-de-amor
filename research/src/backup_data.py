import os

from serenata_toolbox.datasets import Datasets

datasets = Datasets('data')

for file_name in datasets.pending:
    file_path = os.path.join(datasets.local.directory, file_name)
    print('Uploading {}…'.format(file_path))
    datasets.remote.upload(file_path)
