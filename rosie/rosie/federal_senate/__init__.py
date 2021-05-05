from rosie.federal_senate import settings
from rosie.federal_senate.adapter import Adapter
from rosie.core import Core


def main(starting_year, target_directory='/tmp/serenata-data'):
    adapter = Adapter(target_directory, starting_year)
    core = Core(settings, adapter)
    core()
