import sys

import django
from django.core.management.base import BaseCommand
from django.db import connection

from geotrek import __version__


class Command(BaseCommand):
    help = "Check Geotrek-admin, Python, Django, PostgreSQL, PostGIS and pgRouting version used by your system."

    def add_arguments(self, parser):
        parser.add_argument('--geotrek', action='store_true', help="Show only Geotrek version.")
        parser.add_argument('--python', action='store_true', help="Show only Python version.")
        parser.add_argument('--django', action='store_true', help="Show only Django version.")
        parser.add_argument('--postgresql', action='store_true', help="Show only PostgreSQL version.")
        parser.add_argument('--postgis', action='store_true', help="Show only PostGIS version.")
        parser.add_argument('--pgrouting', action='store_true', help="Show only pgRouting version.")
        parser.add_argument('--full', action='store_true', help="Show full version infos.")

    def get_geotrek_version(self):
        return __version__

    def get_python_version(self, full=False):
        if full:
            return sys.version
        else:
            major, minor, micro = sys.version_info[:3]
            return f"{major}.{minor}.{micro}"

    def get_django_version(self):
        return django.get_version()

    def get_postgresql_version(self, full=False):
        with connection.cursor() as cursor:
            if full:
                cursor.execute("SELECT version()")
                return cursor.fetchone()[0]
            else:
                cursor.execute("SHOW server_version")
                return cursor.fetchone()[0].split(' ')[0]

    def get_postgis_version(self, full=False):
        with connection.cursor() as cursor:
            if full:
                cursor.execute("SELECT PostGIS_full_version()")
                return cursor.fetchone()[0]
            else:
                cursor.execute("SELECT PostGIS_version()")
                return cursor.fetchone()[0].split(' ')[0]

    def get_pgrouting_version(self, full=False):
        with connection.cursor() as cursor:
            if full:
                cursor.execute("SELECT pgr_full_version()")
                return cursor.fetchone()[0]
            else:
                cursor.execute("SELECT pgr_version()")
                return cursor.fetchone()[0].split(' ')[0]

    def handle(self, *args, **options):
        full = options['full']

        if options['geotrek']:
            self.stdout.write(self.get_geotrek_version())
            return

        if options['python']:
            self.stdout.write(self.get_python_version(full))
            return

        if options['django']:
            self.stdout.write(self.get_django_version())
            return

        if options['postgresql']:
            self.stdout.write(self.get_postgresql_version(full))
            return

        if options['postgis']:
            self.stdout.write(self.get_postgis_version(full))
            return

        if options['pgrouting']:
            self.stdout.write(self.get_pgrouting_version(full))
            return

        self.stdout.write(f"Geotrek version    : {self.style.SUCCESS(self.get_geotrek_version())}")
        self.stdout.write(f"Python version     : {self.style.SUCCESS(self.get_python_version(full))}")
        self.stdout.write(f"Django version     : {self.style.SUCCESS(self.get_django_version())}")
        self.stdout.write(f"PostgreSQL version : {self.style.SUCCESS(self.get_postgresql_version(full))}")
        self.stdout.write(f"PostGIS version    : {self.style.SUCCESS(self.get_postgis_version(full))}")
        self.stdout.write(f"pgRouting version  : {self.style.SUCCESS(self.get_pgrouting_version(full))}")
        return
