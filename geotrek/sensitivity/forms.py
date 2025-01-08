import logging

from django import forms
from .models import SensitiveArea, SportPractice, Species
from geotrek.common.forms import CommonForm
from django.core.validators import MinValueValidator
from django.utils.translation import pgettext, gettext as _
from mapentity.widgets import MapWidget

logger = logging.getLogger(__name__)


class BubbleMapWidget(MapWidget):
    geometry_field_class = 'bubbleGeometryField'


class PolygonMapWidget(MapWidget):
    geometry_field_class = 'polygonGeometryField'


class SensitiveAreaForm(CommonForm):
    geomfields = ['geom']
    name = forms.CharField(max_length=250, label=_("Name"), required=False)
    species = forms.ModelChoiceField(queryset=Species.objects.filter(category=Species.SPECIES),
                                     label=pgettext("Singular", "Species"))

    class Meta:
        fields = ['structure', 'species', 'name', 'published', 'description', 'contact', 'geom']
        model = SensitiveArea
        widgets = {'geom': BubbleMapWidget()}


class RegulatorySensitiveAreaForm(CommonForm):
    geomfields = ['geom']
    name = forms.CharField(max_length=250, label=_("Name"))
    elevation = forms.IntegerField(label=_("Elevation"), required=False, validators=[MinValueValidator(0)])
    pictogram = forms.FileField(label=_("Pictogram"), required=False)
    period01 = forms.BooleanField(label=_("January"), required=False)
    period02 = forms.BooleanField(label=_("February"), required=False)
    period03 = forms.BooleanField(label=_("March"), required=False)
    period04 = forms.BooleanField(label=_("April"), required=False)
    period05 = forms.BooleanField(label=_("May"), required=False)
    period06 = forms.BooleanField(label=_("June"), required=False)
    period07 = forms.BooleanField(label=_("July"), required=False)
    period08 = forms.BooleanField(label=_("August"), required=False)
    period09 = forms.BooleanField(label=_("September"), required=False)
    period10 = forms.BooleanField(label=_("October"), required=False)
    period11 = forms.BooleanField(label=_("November"), required=False)
    period12 = forms.BooleanField(label=_("Decembre"), required=False)
    practices = forms.ModelMultipleChoiceField(label=_("Sport practices"), queryset=SportPractice.objects)
    url = forms.URLField(label=_("URL"), required=False)

    class Meta:
        fields = ['structure', 'name', 'elevation', 'published', 'description', 'contact', 'pictogram', 'practices', 'rules'] + \
                 ['period{:02}'.format(p) for p in range(1, 13)] + ['url', 'geom']
        model = SensitiveArea
        widgets = {'geom': PolygonMapWidget()}

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            species = instance.species
            kwargs['initial'] = {
                # 'name': species.name,
                'elevation': species.radius,
                'pictogram': species.pictogram,
                'practices': species.practices.all(),
                'url': species.url,
            }
            for p in range(1, 13):
                name = 'period{:02}'.format(p)
                kwargs['initial'][name] = getattr(species, name)

        super().__init__(*args, **kwargs)
        self.helper.form_action += f'?category={Species.REGULATORY}'

    def save(self, **kwargs):
        if not self.instance.pk:
            species = Species()
        else:
            species = self.instance.species
        species.category = Species.REGULATORY
        species.radius = self.cleaned_data['elevation']
        species.pictogram = self.cleaned_data['pictogram']
        species.url = self.cleaned_data['url']
        for p in range(1, 13):
            fieldname = 'period{:02}'.format(p)
            setattr(species, fieldname, self.cleaned_data[fieldname])
        species.save()
        species.practices.set(self.cleaned_data['practices'])
        area = super().save(commit=False)
        area.species = species
        area.save()
        self.save_m2m()
        return area
