#!/usr/bin/python3
import os
import distutils.command.build
from pathlib import Path
from setuptools import setup, find_packages
from shutil import copy

here = os.path.abspath(os.path.dirname(__file__))


class BuildCommand(distutils.command.build.build):
    def run(self):
        distutils.command.build.build.run(self)
        from django.core.management import call_command
        curdir = os.getcwd()
        for subdir in ('geotrek', ):
            os.chdir(subdir)
            call_command('compilemessages')
            for path in Path('.').rglob('*.mo'):
                copy(path, os.path.join(curdir, self.build_lib, subdir, path))
            os.chdir(curdir)


setup(
    name='geotrek',
    version=open(os.path.join(here, 'VERSION')).read().strip(),
    author='Makina Corpus',
    author_email='geobi@makina-corpus.com',
    url='https://makina-corpus.com',
    description="Geotrek",
    scripts=['manage.py'],
    install_requires=[
        'Django==4.2.*',
        'backports-zoneinfo;python_version<"3.10"',  # not directly needed but required to make it worked with 3.10
        'mapentity',
        'chardet',
        'cairosvg',
        'cairocffi',
        'python-dotenv',
        # pinned by requirements.txt
        'pymemcache',
        'coreschema',
        'coreapi',
        'psycopg2',
        'pdfimpose',
        'docutils',
        'Pillow',
        'simplekml',
        'pygal',
        'paperclip',
        'django-extended-choices',
        'django-modelcluster',
        'django-mptt',
        'geojson',
        'tif2geojson',
        'drf-dynamic-fields',
        'drf-yasg',
        'xlrd',
        'landez',
        'large-image-source-vips',
        'django-large-image',
        'celery',
        'redis',
        'django-celery-results',
        'drf-extensions',
        'django-colorfield',
        'Fiona',
        'markdown',
        "weasyprint==52.5",  # newer version required libpango (not available in bionic)
        'django-weasyprint<3.0.0',  # 2.10 require weasyprint > 53
        "django-clearcache",
        "pyopenair",
        "django-treebeard",
        # prod,
        'gunicorn',
        'sentry-sdk',
        'easy-thumbnails[svg]',
    ],
    cmdclass={"build": BuildCommand},
    include_package_data=True,
    license='BSD, see LICENSE file.',
    packages=find_packages(),
    classifiers=['Natural Language :: English',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Development Status :: 5 - Production/Stable',
                 'Programming Language :: Python :: 3'],
)
