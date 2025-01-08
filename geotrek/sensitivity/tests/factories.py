import factory

from django.contrib.auth.models import Permission

from geotrek.authent.tests.factories import StructureRelatedDefaultFactory
from geotrek.common.utils.testdata import get_dummy_uploaded_image

from .. import models

from mapentity.tests.factories import UserFactory


class RuleFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Rule %s' % n)
    code = factory.Sequence(lambda n: 'CODE%s' % n)
    url = factory.faker.Faker('url')
    pictogram = factory.django.ImageField()

    class Meta:
        model = models.Rule
        django_get_or_create = ('code', )


class SportPracticeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SportPractice

    name = "Practice"


class SpeciesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Species

    name = "Species"
    pictogram = get_dummy_uploaded_image()
    url = "http://url.com"
    period06 = True
    period07 = True
    category = models.Species.SPECIES

    @factory.post_generation
    def practices(obj, create, extracted=None, **kwargs):
        if create:
            if not extracted:
                practices = [
                    SportPracticeFactory.create(name="Practice1"),
                    SportPracticeFactory.create(name="Practice2"),
                ]
            for practice in practices:
                obj.practices.add(practice)


class RegulatorySpeciesFactory(SpeciesFactory):
    category = models.Species.REGULATORY


class SensitiveAreaFactory(StructureRelatedDefaultFactory):
    class Meta:
        model = models.SensitiveArea

    species = factory.SubFactory(SpeciesFactory)
    geom = 'POLYGON((700000 6600000, 700000 6600003, 700003 6600003, 700003 6600000, 700000 6600000))'
    published = True
    description = "Blabla"
    contact = "<a href=\"mailto:toto@tata.com\">toto@tata.com</a>"

    @factory.post_generation
    def rules(obj, create, extracted=None, **kwargs):
        if create:
            if not extracted:
                rules = [
                    RuleFactory.create(
                        code='R1',
                        name='Rule1',
                        url='http://url.com',
                        pictogram='picto_rule1.png'
                    ),
                    RuleFactory.create(
                        code='R2',
                        name='Rule2',
                        url='http://url.com',
                        pictogram='picto_rule2.png',
                        description="abcdefgh"
                    ),
                ]
            for rule in rules:
                obj.rules.add(rule)


class MultiPolygonSensitiveAreaFactory(SensitiveAreaFactory):
    geom = 'MULTIPOLYGON(((700000 6600000, 700000 6600003, 700003 6600003, 700003 6600000, 700000 6600000)),' \
        '((700010 6600010, 700010 6600013, 700013 6600013, 700013 6600010, 700010 6600010)))'


class RegulatorySensitiveAreaFactory(SensitiveAreaFactory):
    species = factory.SubFactory(RegulatorySpeciesFactory)


class BiodivManagerFactory(UserFactory):
    is_staff = True

    @factory.post_generation
    def create_biodiv_manager(obj, create, extracted, **kwargs):
        for perm in Permission.objects.exclude(codename='can_bypass_structure'):
            obj.user_permissions.add(perm)
