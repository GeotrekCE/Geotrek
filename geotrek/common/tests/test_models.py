from geotrek.authent.models import Structure
from geotrek.common.tests.factories import LabelFactory, OrganismFactory
from geotrek.common.models import Theme
from django.conf import settings
from django.core.files import File
from django.test import TestCase
import os


class ThemeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        cls.files = [f for f in os.listdir(cls.directory)]

    def test_pictogram(self):
        self.path = os.path.join(self.directory, 'picto.png')
        self.assertEqual(os.path.getsize(self.path), 6203)
        self.theme = Theme.objects.create()
        with open(self.path, 'rb') as picto_file:
            self.theme.pictogram = File(picto_file)
            file = self.theme.pictogram_off
            path_off = os.path.join(self.directory, 'picto_off.png')
            self.assertEqual(os.path.getsize(path_off), 3445)
            self.assertEqual(file.name, path_off)

    def tearDown(self):
        for f in os.listdir(self.directory):
            if f not in self.files:
                os.remove(os.path.join(self.directory, f))


class LabelTest(TestCase):
    def test_str(self):
        label = LabelFactory.create(name="foo")
        self.assertEqual(str(label), "foo")


class OrganismTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organism_with_structure = OrganismFactory.create(structure=Structure.objects.get(pk=settings.DEFAULT_STRUCTURE_PK))
        cls.organism_without_structure = OrganismFactory.create()

    def test_str_with_structure(self):
        self.assertEqual(
            f"{self.organism_with_structure}",
            f"{self.organism_with_structure.organism} ({self.organism_with_structure.structure.name})"
        )

    def test_str_without_structure(self):
        self.assertEqual(f"{self.organism_without_structure}", self.organism_without_structure.organism)
