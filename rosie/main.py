import sys
from dataset import Dataset
from rosie import Rosie

DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else '/tmp/serenata-data'


if __name__ == '__main__':
    dataset = Dataset(DATA_PATH).get()
    Rosie(dataset, DATA_PATH).run_classifiers()
