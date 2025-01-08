from django.core.management.base import BaseCommand

from geotrek.core.path_router import PathRouter


class Command(BaseCommand):
    help = """
    Generates the paths graph (pgRouting network topology) by filling
    columns source and target of the core_path table.
    """

    def handle(self, *args, **options):
        PathRouter()  # PathRouter's init method builds the network topology
