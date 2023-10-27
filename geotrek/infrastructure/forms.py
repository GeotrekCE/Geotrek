from crispy_forms.layout import Div
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from mapentity.widgets import MapWidget

from ..common.mixins.forms import CommonForm
from geotrek.core.forms import TopologyForm

from .models import Infrastructure

if settings.TREKKING_TOPOLOGY_ENABLED:
    class BaseInfrastructureForm(TopologyForm):
        implantation_year = forms.IntegerField(label=_("Implantation year"), required=False)

        class Meta(TopologyForm.Meta):
            fields = TopologyForm.Meta.fields + \
                ['structure', 'name', 'description', 'type', 'condition', 'access', 'implantation_year', 'published']
else:
    class BaseInfrastructureForm(CommonForm):

        implantation_year = forms.IntegerField(label=_("Implantation year"), required=False)
        geomfields = ['geom']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            modifiable = self.fields['geom'].widget.modifiable
            self.fields['geom'].widget = MapWidget(attrs={'geom_type': 'POINT'})
            self.fields['geom'].widget.modifiable = modifiable

        class Meta(CommonForm.Meta):
            model = Infrastructure
            fields = CommonForm.Meta.fields + ['geom', 'structure', 'name', 'description', 'type', 'condition', 'access',
                                               'implantation_year', 'published']


class InfrastructureForm(BaseInfrastructureForm):

    fieldslayout = [
        Div(
            'structure',
            'name',
            'description',
            'accessibility',
            'type',
            'condition',
            'access',
            'implantation_year',
            'usage_difficulty',
            'maintenance_difficulty',
            'published',
        )
    ]

    class Meta(BaseInfrastructureForm.Meta):
        model = Infrastructure
        fields = BaseInfrastructureForm.Meta.fields + ['accessibility', 'maintenance_difficulty', 'usage_difficulty']
