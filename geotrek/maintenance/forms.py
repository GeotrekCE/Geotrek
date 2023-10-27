from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import FloatField
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from ..common.mixins.forms import CommonForm
from geotrek.core.fields import TopologyField
from geotrek.core.models import Topology
from geotrek.feedback.models import WorkflowManager

from .models import Intervention, InterventionJob, ManDay, Project

if 'geotrek.feedback' in settings.INSTALLED_APPS:
    from geotrek.feedback.models import Report, ReportStatus, TimerEvent


class ManDayForm(forms.ModelForm):

    class Meta:
        model = ManDay
        fields = ('id', 'nb_days', 'job')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout('id', 'nb_days', 'job')
        self.fields['nb_days'].widget.attrs['placeholder'] = _('Days')
        self.fields['nb_days'].label = ''
        self.fields['nb_days'].widget.attrs['class'] = 'input-mini'
        self.fields['job'].widget.attrs['class'] = 'input-medium'
        if self.instance and self.instance.pk:
            self.fields['job'].queryset = InterventionJob.objects.filter(Q(active=True) | Q(id=self.instance.job_id))
        else:
            self.fields['job'].queryset = InterventionJob.objects.filter(active=True)


ManDayFormSet = inlineformset_factory(Intervention, Intervention.jobs.through, form=ManDayForm, extra=1)


class FundingForm(forms.ModelForm):

    class Meta:
        fields = ('id', 'amount', 'organism')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout('id', 'amount', 'organism')
        self.fields['organism'].widget.attrs['class'] = 'input-xlarge'


FundingFormSet = inlineformset_factory(Project, Project.founders.through, form=FundingForm, extra=1)


class InterventionForm(CommonForm):
    """ An intervention can be a Point or a Line """

    topology = TopologyField(label="")
    length = FloatField(required=False, label=_("Length"))
    project = forms.ModelChoiceField(required=False, label=_("Project"),
                                     queryset=Project.objects.existing())

    geomfields = ['topology']
    leftpanel_scrollable = False

    fieldslayout = [
        Div(
            'structure',
            'name',
            'date',
            'status',
            'disorders',
            'type',
            'subcontracting',
            'length',
            'width',
            'height',
            'stake',
            'project',
            'description',
            'material_cost',
            'heliport_cost',
            'subcontract_cost',
            Fieldset(_("Mandays")),
            css_class="scrollable tab-pane active"
        ),
    ]

    class Meta(CommonForm.Meta):
        model = Intervention
        fields = CommonForm.Meta.fields + \
            ['structure', 'name', 'date', 'status', 'disorders', 'type', 'description', 'subcontracting', 'length', 'width',
             'height', 'stake', 'project', 'material_cost', 'heliport_cost', 'subcontract_cost', 'topology']

    def __init__(self, *args, target_type=None, target_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            # New intervention. We have to set its target.
            if target_type and target_id:
                # Point target to an existing topology
                ct = ContentType.objects.get_for_id(target_type)
                self.instance.target = ct.get_object_for_this_type(id=target_id)
                # Set POST URL
                self.helper.form_action += '?target_type={}&target_id={}'.format(target_type, target_id)
            else:
                # Point target to a new topology
                self.instance.target = Topology(kind='INTERVENTION')
        # Else: existing intervention. Target is already set

        self.fields['topology'].initial = self.instance.target

        if self.instance.target.__class__ == Topology:
            # Intervention has its own topology
            title = _("On {}".format(_("Paths")))
            self.fields['topology'].label = \
                '<img src="{prefix}images/path-16.png" title="{title}">{title}'.format(
                    prefix=settings.STATIC_URL, title=title
            )
        else:
            # Intervention on an existing topology
            icon = self.instance.target._meta.model_name
            title = _("On {}".format(str(self.instance.target)))
            self.fields['topology'].label = \
                '<img src="{prefix}images/{icon}-16.png" title="{title}"><a href="{url}">{title}</a>'.format(
                    prefix=settings.STATIC_URL, icon=icon, title=title,
                    url=self.instance.target.get_detail_url()
            )
            # Topology is readonly
            del self.fields['topology']

        # Length is not editable in AltimetryMixin
        self.fields['length'].initial = self.instance.length
        editable = bool(self.instance.geom and (self.instance.geom.geom_type == 'Point'
                        or self.instance.geom.geom_type == 'LineString'))
        self.fields['length'].widget.attrs['readonly'] = editable

    def save(self, *args, **kwargs):
        target = self.instance.target
        if 'geotrek.feedback' in settings.INSTALLED_APPS and settings.SURICATE_WORKFLOW_ENABLED and isinstance(target, Report):
            # If this is an intervention programmed for a report, change report status
            if 'status' in self.changed_data and self.instance.status.order == 20:
                programmed_status = ReportStatus.objects.get(identifier='programmed')
                target.status = programmed_status
                target.save()
                TimerEvent.objects.create(step=programmed_status, report=target)
            # If this is an intervention being resolved for a report, change report status and notify
            elif 'status' in self.changed_data and self.instance.status.order == 30:
                resolved_status = ReportStatus.objects.get(identifier='solved_intervention')
                target.status = resolved_status
                if not settings.SURICATE_WORKFLOW_SETTINGS.get("SKIP_MANAGER_MODERATION"):
                    target.assigned_user = WorkflowManager.objects.first().user
                target.save()
                if not settings.SURICATE_WORKFLOW_SETTINGS.get("SKIP_MANAGER_MODERATION"):
                    WorkflowManager.objects.first().notify_report_to_solve(target)
        if not target.pk:
            target.save()
        topology = self.cleaned_data.get('topology')
        if topology and topology.pk != target.pk:
            target.mutate(topology)
        intervention = super().save(*args, **kwargs, commit=False)
        intervention.target = target
        intervention.save()
        self.save_m2m()
        return intervention


class ProjectForm(CommonForm):
    fieldslayout = [
        Div(
            Div(
                Div('structure',
                    'name',
                    'type',
                    'domain',
                    'begin_year',
                    'end_year',
                    'constraint',
                    'global_cost',
                    'comments',

                    css_class="span6"),
                Div('project_owner',
                    'project_manager',
                    'contractors',
                    Fieldset(_("Fundings")),
                    css_class="span6"),
                css_class="row-fluid"
            ),
            css_class="container-fluid"
        ),
    ]

    class Meta(CommonForm.Meta):
        model = Project
        fields = CommonForm.Meta.fields + \
            ['structure', 'name', 'type', 'domain', 'begin_year', 'end_year', 'constraint',
             'global_cost', 'comments', 'project_owner', 'project_manager', 'contractors']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_tag = False

    def clean(self, *args, **kwargs):
        clean_data = super().clean(*args, **kwargs)

        if clean_data.get("end_year") and clean_data.get("end_year") < clean_data.get("begin_year"):
            self.add_error('end_year', _('Start year is after end year'))
