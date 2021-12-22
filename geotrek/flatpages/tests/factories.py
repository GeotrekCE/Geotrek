import factory

from geotrek.flatpages import models as flatpages_models


class FlatPageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = flatpages_models.FlatPage

    title = factory.Sequence(lambda n: "Page %s" % n)
    content = factory.Sequence(lambda n: "<h1>Titre %s</h1>" % n)
    order = factory.Sequence(lambda n: n)

    @factory.post_generation
    def sources(obj, create, extracted=None, **kwargs):
        if create and extracted:
            obj.source.set(extracted)

    @factory.post_generation
    def portals(obj, create, extracted=None, **kwargs):
        if create and extracted:
            obj.portal.set(extracted)
