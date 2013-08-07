from django import forms
from geotrek.core.forms import TopologyForm
from geotrek.core.widgets import PointTopologyWidget

from .models import Infrastructure, InfrastructureType, Signage


class BaseInfrastructureForm(TopologyForm):
    class Meta(TopologyForm.Meta):
        fields = TopologyForm.Meta.fields + \
            ['structure',
             'name', 'description', 'type']


class InfrastructureForm(BaseInfrastructureForm):
    def __init__(self, *args, **kwargs):
        super(InfrastructureForm, self).__init__(*args, **kwargs)
        qs = InfrastructureType.objects.for_infrastructures()
        self.fields['type'] = forms.ModelChoiceField(queryset=qs)

    class Meta(BaseInfrastructureForm.Meta):
        model = Infrastructure


class SignageForm(BaseInfrastructureForm):
    def __init__(self, *args, **kwargs):
        super(SignageForm, self).__init__(*args, **kwargs)
        self.fields['topology'].widget = PointTopologyWidget()
        qs = InfrastructureType.objects.for_signages()
        self.fields['type'] = forms.ModelChoiceField(queryset=qs)

    class Meta(BaseInfrastructureForm.Meta):
        model = Signage
