import factory
from geotrek.authent.tests.factories import UserFactory
from geotrek.common.models import Attachment
from geotrek.common.utils.testdata import (dummy_filefield_as_sequence,
                                           get_dummy_uploaded_image,
                                           get_dummy_uploaded_file)

from .. import models


class OrganismFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Organism

    organism = factory.Sequence(lambda n: "Organism %s" % n)


class FileTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FileType

    type = factory.Sequence(lambda n: "FileType %s" % n)


class LicenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.License

    label = factory.Sequence(lambda n: "License %s" % n)


class AttachmentFactory(factory.django.DjangoModelFactory):
    """
    Create an attachment. You must provide an 'obj' keywords,
    the object (saved in db) to which the attachment will be bound.
    """

    class Meta:
        model = Attachment

    attachment_file = get_dummy_uploaded_file()
    filetype = factory.SubFactory(FileTypeFactory)
    license = factory.SubFactory(LicenseFactory)

    creator = factory.SubFactory(UserFactory)
    title = factory.Sequence("Title {0}".format)
    legend = factory.Sequence("Legend {0}".format)


class ThemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Theme

    label = factory.Sequence(lambda n: "Theme %s" % n)
    pictogram = dummy_filefield_as_sequence('theme-%s.png')


class RecordSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RecordSource

    name = factory.Sequence(lambda n: "Record source %s" % n)
    website = 'http://geotrek.fr'
    pictogram = dummy_filefield_as_sequence('recordsource-%s.png')


class TargetPortalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TargetPortal

    name = factory.Sequence(lambda n: "Target Portal %s" % n)
    website = factory.Sequence(lambda n: "http://geotrek-rando-{}.fr".format(n))


class ReservationSystemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ReservationSystem

    name = factory.Sequence(lambda n: "Reservation system %s" % n)


class LabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Label

    name = "Label"
    pictogram = get_dummy_uploaded_image('label.png')
    advice = "Advice label"
    filter = True
    published = True


class AttachmentAccessibilityFactory(factory.django.DjangoModelFactory):
    """
    Create an attachment. You must provide an 'obj' keywords,
    the object (saved in db) to which the attachment will be bound.
    """

    class Meta:
        model = models.AccessibilityAttachment

    attachment_accessibility_file = get_dummy_uploaded_image()

    creator = factory.SubFactory(UserFactory)
    title = factory.Sequence("Title {0}".format)
    legend = factory.Sequence("Legend {0}".format)


class HDViewPointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.HDViewPoint
    picture = get_dummy_uploaded_image()
    title = "A title"
    author = "An author"
    legend = "Something"
    geom = "SRID=2154;POINT(0 0)"
    annotations = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                7997.087502861313,
                                6997.090981210413
                            ],
                            [
                                7997.087502861313,
                                6456.7472299480705
                            ],
                            [
                                8631.090837675794,
                                6456.7472299480705
                            ],
                            [
                                8631.090837675794,
                                6997.090981210413
                            ],
                            [
                                7997.087502861313,
                                6997.090981210413
                            ]
                        ]
                    ]
                },
                "properties": {
                    "annotationType": "ellipse",
                    "name": "Ellipse 1",
                    "annotationId": 1
                }
            }
        ]
    }


class AccessMeanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.AccessMean

    label = factory.Sequence(lambda n: "Acces mean %s" % n)
