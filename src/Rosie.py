import os
from serenata_toolbox.ceap_dataset import CEAPDataset

class Rosie:
    DATA_PATH = '/tmp/serenata-data'

    def update_datasets(self):
        os.makedirs(self.DATA_PATH, exist_ok=True)
        ceap = CEAPDataset(self.DATA_PATH)
        ceap.fetch()
        ceap.convert_to_csv()
        ceap.translate()
        ceap.clean()



if __name__ == '__main__':
    rosie = Rosie()
    rosie.update_datasets()
