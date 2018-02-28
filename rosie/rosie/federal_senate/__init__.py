from rosie.federal_senate import settings
from rosie.federal_senate.adapter import Adapter
from rosie.core import Core


def main(target_directory='/tmp/serenata-data'):
    adapter = Adapter(target_directory)
    core = Core(settings, adapter)
    core()