# -*- coding: utf-8 -*-

import factory

from geotrek.authent.factories import StructureRelatedDefaultFactory
from geotrek.common.utils.testdata import dummy_filefield_as_sequence

from . import models


class SportPracticeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.SportPractice

    name = factory.Sequence(lambda n: u"Practice %s" % n)


class SpeciesFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Species

    name = factory.Sequence(lambda n: u"Species %s" % n)
    pictogram = dummy_filefield_as_sequence('thumbnail %s')
    url = factory.Sequence(lambda n: u"http://url%s.com" % n)
    period06 = True
    period07 = True
    category = models.Species.SPECIES

    @factory.post_generation
    def create_practices(obj, create, extracted, **kwargs):
        practices = kwargs.pop('practices', None)

        if create:
            if practices is None:
                practices = [SportPracticeFactory.create(), SportPracticeFactory.create()]
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


class RegulatorySensitiveAreaFactory(SensitiveAreaFactory):
    species = factory.SubFactory(RegulatorySpeciesFactory)
