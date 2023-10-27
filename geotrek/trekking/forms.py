from copy import deepcopy

from django.utils.translation import gettext as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Layout, Submit, HTML, Div, Fieldset
from mapentity.forms import TranslatedModelForm
from mapentity.widgets import SelectMultipleWithPop, MapWidget

from ..common.mixins.forms import CommonForm
from geotrek.core.forms import TopologyForm
from geotrek.core.widgets import LineTopologyWidget, PointTopologyWidget
from .models import Trek, POI, WebLink, Service, ServiceType, OrderedTrekChild, RatingScale
from django.db import transaction


class TrekRelationshipForm(forms.ModelForm):
    trek_b = forms.ModelChoiceField(queryset=Trek.objects.existing(), required=True,
                                    label=_("Trek"))

    class Meta:
        fields = ('id',
                  'trek_a',
                  'trek_b',
                  'has_common_departure',
                  'has_common_edge',
                  'is_circuit_step')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout('id',
                                    'trek_a',
                                    'trek_b',
                                    'has_common_departure',
                                    'has_common_edge',
                                    'is_circuit_step',
                                    'DELETE')


TrekRelationshipFormSet = inlineformset_factory(Trek, Trek.related_treks.through,
                                                form=TrekRelationshipForm, fk_name='trek_a',
                                                extra=1)

if settings.TREKKING_TOPOLOGY_ENABLED:

    class BaseTrekForm(TopologyForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            modifiable = self.fields['topology'].widget.modifiable
            # TODO: We should change LeafletWidget to keep modifiable.
            # Init of TopologyForm -> commonForm -> mapentityForm
            # already add a leafletwidget with modifiable
            self.fields['topology'].widget = LineTopologyWidget()
            self.fields['topology'].widget.modifiable = modifiable
            self.fields['points_reference'].label = ''
            self.fields['points_reference'].widget.target_map = 'topology'
            self.fields['parking_location'].label = ''
            self.fields['parking_location'].widget.target_map = 'topology'

        class Meta(TopologyForm.Meta):
            model = Trek
else:

    class BaseTrekForm(CommonForm):
        geomfields = ['geom']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            modifiable = self.fields['geom'].widget.modifiable
            self.fields['geom'].widget = MapWidget(attrs={'geom_type': 'LINESTRING'})
            self.fields['geom'].widget.modifiable = modifiable
            self.fields['points_reference'].label = ''
            self.fields['points_reference'].widget.target_map = 'geom'
            self.fields['parking_location'].label = ''
            self.fields['parking_location'].widget.target_map = 'geom'

        class Meta(CommonForm.Meta):
            model = Trek
            fields = CommonForm.Meta.fields + ['geom']


class TrekForm(BaseTrekForm):
    children_trek = forms.ModelMultipleChoiceField(label=_("Children"),
                                                   queryset=Trek.objects.all(), required=False,
                                                   help_text=_("Select children in order"))
    hidden_ordered_children = forms.CharField(label=_("Hidden ordered children"),
                                              widget=forms.widgets.HiddenInput(),
                                              required=False)

    leftpanel_scrollable = False

    base_fieldslayout = [
        Div(
            HTML(
                """<ul class="nav nav-tabs">
    <li id="tab-main" class="nav-item">
        <a class="nav-link active" href="#main" data-toggle="tab"><i class="bi bi-card-list"></i> {0}</a>
    </li>
    <li id="tab-advanced" class="nav-item">
        <a class="nav-link" href="#advanced" data-toggle="tab"><i class="bi bi-list-ul"></i> {1}</a>
    </li>
    <li id="tab-accessibility" class="nav-item">
        <a class="nav-link" href="#accessibility" data-toggle="tab"><i class="bi bi-eye-slash-fill"></i> {2}</a>
    </li>
</ul>""".format(_("Main"), _("Advanced"), _("Accessibility"))),
            Div(
                Div(
                    'name',
                    'review',
                    'published',
                    'departure',
                    'arrival',
                    'duration',
                    'difficulty',
                    'practice',
                    'ratings_description',
                    'route',
                    'access',
                    'description_teaser',
                    'ambiance',
                    'description',
                    css_id="main",
                    css_class="scrollable tab-pane active"
                ),
                Div(
                    'points_reference',
                    'advised_parking',
                    'parking_location',
                    'public_transport',
                    'advice',
                    'gear',
                    'themes',
                    'labels',
                    'networks',
                    'web_links',
                    'information_desks',
                    'source',
                    'portal',
                    'children_trek',
                    'eid',
                    'eid2',
                    'reservation_system',
                    'reservation_id',
                    'pois_excluded',
                    'hidden_ordered_children',
                    Fieldset(_("Related treks"),),
                    css_id="advanced",  # used in Javascript for activating tab if error
                    css_class="scrollable tab-pane"
                ),
                Div(
                    'accessibilities',
                    'accessibility_level',
                    'accessibility_infrastructure',
                    'accessibility_slope',
                    'accessibility_covering',
                    'accessibility_exposure',
                    'accessibility_width',
                    'accessibility_advice',
                    'accessibility_signage',
                    css_id="accessibility",  # used in Javascript for activating tab if error
                    css_class="scrollable tab-pane"
                ),
                css_class="tab-content"
            ),
            css_class="tabbable"
        ),
    ]

    def __init__(self, *args, **kwargs):
        self.fieldslayout = deepcopy(self.base_fieldslayout)
        self.fieldslayout[0][1][0].append(HTML(
            '<div class="controls">{}{}</div>'.format(
                _('Insert service:'),
                ''.join([f'<a class="servicetype" data-url="{t.pictogram.url}" data-name={t.name}">'
                         f'<img src="{t.pictogram.url}"></a>' for t in ServiceType.objects.all()])))
        )
        super().__init__(*args, **kwargs)
        if self.fields.get('structure'):
            self.fieldslayout[0][1][0].insert(0, 'structure')
        self.fields['web_links'].widget = SelectMultipleWithPop(choices=self.fields['web_links'].choices,
                                                                add_url=WebLink.get_add_url())
        # Make sure (force) that name is required, in default language only
        self.fields['name_%s' % settings.LANGUAGE_CODE].required = True

        if not settings.TREK_POINTS_OF_REFERENCE_ENABLED:
            self.fields.pop('points_reference')
        else:
            # Edit points of reference with custom edition JavaScript class
            self.fields['points_reference'].widget.geometry_field_class = 'PointsReferenceField'

        self.fields['parking_location'].widget.geometry_field_class = 'ParkingLocationField'
        self.fields['duration'].widget.attrs['min'] = '0'

        # Since we use chosen() in trek_form.html, we don't need the default help text
        for f in ['themes', 'networks', 'accessibilities',
                  'web_links', 'information_desks', 'source', 'portal']:
            self.fields[f].help_text = ''

        if self.instance:
            queryset_children = OrderedTrekChild.objects.filter(parent__id=self.instance.pk)\
                                                        .order_by('order')
            # init multiple children field with data
            self.fields['children_trek'].queryset = Trek.objects.existing().exclude(pk=self.instance.pk)
            self.fields['children_trek'].initial = [c.child.pk for c in self.instance.trek_children.all()]

            # init hidden field with children order
            self.fields['hidden_ordered_children'].initial = ",".join(str(x) for x in queryset_children.values_list('child__id', flat=True))

        for scale in RatingScale.objects.all():
            ratings = None
            if self.instance.pk:
                ratings = self.instance.ratings.filter(scale=scale)
            fieldname = f'rating_scale_{scale.pk}'
            self.fields[fieldname] = forms.ModelChoiceField(
                label=scale.name,
                queryset=scale.ratings.all(),
                required=False,
                initial=ratings[0] if ratings else None
            )
            right_after_type_index = self.fieldslayout[0][1][0].fields.index('practice') + 1
            self.fieldslayout[0][1][0].insert(right_after_type_index, fieldname)

        if self.instance.pk:
            self.fields['pois_excluded'].queryset = self.instance.all_pois.all()
        else:
            self.fieldslayout[0][1][1].remove('pois_excluded')

    def clean(self):
        cleaned_data = super().clean()
        practice = self.cleaned_data['practice']
        for scale in RatingScale.objects.all():
            if self.cleaned_data.get(f'rating_scale_{scale.pk}'):
                try:
                    practice.rating_scales.get(pk=scale.pk)
                except RatingScale.DoesNotExist:
                    raise ValidationError(_("One of the rating scale used is not part of the practice chosen"))
        return cleaned_data

    def clean_children_trek(self):
        """
        Check the trek is not parent and child at the same time
        """
        children = self.cleaned_data['children_trek']
        if children and self.instance and self.instance.trek_parents.exists():
            raise ValidationError(_("Cannot add children because this trek is itself a child."))
        for child in children:
            if child.trek_children.exists():
                raise ValidationError(_(f"Cannot use parent trek {child.name} as a child trek."))
        return children

    def save(self, *args, **kwargs):
        """
        Custom form save override - ordered children management
        """
        sid = transaction.savepoint()

        try:
            return_value = super().save(self, *args, **kwargs)
            # Save ratings
            # TODO : Go through practice and not rating_scales
            if return_value.practice:
                field = getattr(return_value, 'ratings')
                to_remove = list(field.exclude(scale__practice=return_value.practice).values_list('pk', flat=True))
                to_add = []
                for scale in return_value.practice.rating_scales.all():
                    rating = self.cleaned_data.get(f'rating_scale_{scale.pk}')
                    needs_removal = field.filter(scale=scale)
                    if rating:
                        needs_removal = needs_removal.exclude(pk=rating.pk)
                        to_add.append(rating.pk)
                    to_remove += list(needs_removal.values_list('pk', flat=True))
                field.remove(*to_remove)
                field.add(*to_add)

            # save ordered children
            ordering = []

            if self.cleaned_data['hidden_ordered_children']:
                ordering = self.cleaned_data['hidden_ordered_children'].split(',')

            order = 0

            # add and update
            for value in ordering:
                child, created = OrderedTrekChild.objects.get_or_create(parent=self.instance,
                                                                        child=Trek.objects.get(pk=value))
                child.order = order
                child.save()
                order += 1

            # delete
            new_list_children = self.cleaned_data['children_trek'].values_list('pk', flat=True)

            for child_relation in self.instance.trek_children.all():
                # if existant child not in selection, deletion
                if child_relation.child_id not in new_list_children:
                    child_relation.delete()

            transaction.savepoint_commit(sid)
            return return_value

        except Exception as exc:
            transaction.savepoint_rollback(sid)
            raise exc

    class Meta(BaseTrekForm.Meta):
        fields = BaseTrekForm.Meta.fields + \
            ['structure', 'name', 'review', 'published', 'labels', 'departure',
             'arrival', 'duration', 'difficulty', 'route', 'ambiance',
             'access', 'description_teaser', 'description', 'ratings_description', 'points_reference',
             'accessibility_infrastructure', 'advised_parking', 'parking_location',
             'public_transport', 'advice', 'gear', 'themes', 'networks', 'practice', 'accessibilities',
             'accessibility_level', 'accessibility_signage', 'accessibility_slope', 'accessibility_covering',
             'accessibility_exposure', 'accessibility_width', 'accessibility_advice', 'web_links',
             'information_desks', 'source', 'portal', 'children_trek', 'eid', 'eid2', 'reservation_system',
             'reservation_id', 'pois_excluded', 'hidden_ordered_children']


if settings.TREKKING_TOPOLOGY_ENABLED:

    class BasePOIForm(TopologyForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            modifiable = self.fields['topology'].widget.modifiable
            self.fields['topology'].widget = PointTopologyWidget()
            self.fields['topology'].widget.modifiable = modifiable

        class Meta(TopologyForm.Meta):
            model = POI

else:

    class BasePOIForm(CommonForm):
        geomfields = ['geom']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            modifiable = self.fields['geom'].widget.modifiable
            self.fields['geom'].widget = MapWidget(attrs={'geom_type': 'POINT'})
            self.fields['geom'].widget.modifiable = modifiable

        class Meta(CommonForm.Meta):
            model = POI
            fields = CommonForm.Meta.fields + ['geom']


class POIForm(BasePOIForm):
    fieldslayout = [
        Div(
            'structure',
            'name',
            'review',
            'published',
            'type',
            'description',
            'eid',
        )
    ]

    class Meta(BasePOIForm.Meta):
        fields = BasePOIForm.Meta.fields + ['structure', 'name', 'description', 'eid', 'type', 'published', 'review']


if settings.TREKKING_TOPOLOGY_ENABLED:

    class BaseServiceForm(TopologyForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            modifiable = self.fields['topology'].widget.modifiable
            self.fields['topology'].widget = PointTopologyWidget()
            self.fields['topology'].widget.modifiable = modifiable

        class Meta(TopologyForm.Meta):
            model = Service

else:

    class BaseServiceForm(CommonForm):
        geomfields = ['geom']

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            modifiable = self.fields['geom'].widget.modifiable
            self.fields['geom'].widget = MapWidget(attrs={'geom_type': 'POINT'})
            self.fields['geom'].widget.modifiable = modifiable

        class Meta(CommonForm.Meta):
            model = Service
            fields = CommonForm.Meta.fields + ['geom']


class ServiceForm(BaseServiceForm):
    fieldslayout = [
        Div(
            'structure',
            'type',
            'eid',
        )
    ]

    class Meta(BaseServiceForm.Meta):
        fields = BaseServiceForm.Meta.fields + ['structure', 'type', 'eid']


class WebLinkCreateFormPopup(TranslatedModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = self.instance.get_add_url()
        # Main form layout
        # Adds every name field explicitly (name_fr, name_en, ...)
        self.helper.form_class = 'form-horizontal'
        arg_list = [f'name_{language[0]}' for language in settings.MAPENTITY_CONFIG['TRANSLATED_LANGUAGES']]
        arg_list += ['url', 'category', FormActions(
            HTML('<a href="#" class="btn" onclick="javascript:window.close();">%s</a>' % _("Cancel")),
            Submit('save_changes', _('Create'), css_class="btn-primary"),
            css_class="form-actions",
        )]
        self.helper.layout = Layout(*arg_list)

    class Meta:
        model = WebLink
        fields = ['name', 'url', 'category']
