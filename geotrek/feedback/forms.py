from django import forms
from crispy_forms.layout import Div
from django.conf import settings
from django.forms.fields import CharField
from django.forms.widgets import HiddenInput, Textarea
from django.utils.translation import gettext as _

from ..common.mixins.forms import CommonForm

from .models import PredefinedEmail, Report, ReportStatus, TimerEvent, WorkflowDistrict, WorkflowManager


class ReportForm(CommonForm):
    geomfields = ["geom"]

    fieldslayout = [
        Div(
            "email",
            "comment",
            "activity",
            "category",
            "problem_magnitude",
            "related_trek",
            "status",
            "assigned_user",
            "uses_timers"
        )
    ]

    class Meta:
        fields = [
            "geom",
            "email",
            "comment",
            "activity",
            "category",
            "problem_magnitude",
            "related_trek",
            "status",
            "assigned_user",
            "uses_timers"
        ]
        model = Report

    def __init__(self, *args, **kwargs):
        # This dict stores constraints for status changes in management workflow
        # {'current_status': ['allowed_next_status', 'other_allowed_status']}
        # Empty status should not be changed from this form
        suricate_workflow_steps = {
            'filed': ['classified', 'filed', 'rejected'],
            'solved_intervention': ['solved', 'solved_intervention'],
        }
        if settings.SURICATE_WORKFLOW_SETTINGS.get("SKIP_MANAGER_MODERATION"):
            suricate_workflow_steps = {
                'filed': ['classified', 'filed', 'rejected', 'waiting'],
                'solved_intervention': ['solved', 'solved_intervention'],
            }
        super().__init__(*args, **kwargs)
        if settings.SURICATE_WORKFLOW_ENABLED and settings.SURICATE_WORKFLOW_SETTINGS.get("SKIP_MANAGER_MODERATION"):
            self.user = kwargs['user']
        self.fields["geom"].required = True
        # Store current status
        if self.instance.pk:
            self.old_status = self.instance.status
        if settings.SURICATE_WORKFLOW_ENABLED:  # On Management or Workflow modes
            if self.instance.pk:  # On updates
                # Hide fields that are handled automatically in these modes
                self.fields["email"].widget = HiddenInput()
                self.fields["comment"].widget = HiddenInput()
                self.fields["activity"].widget = HiddenInput()
                self.fields["category"].widget = HiddenInput()
                self.fields["problem_magnitude"].widget = HiddenInput()
                if settings.SURICATE_WORKFLOW_ENABLED:  # On Workflow
                    self.old_supervisor = self.instance.assigned_user
                    # Add fields that are used only in Workflow mode
                    # status
                    next_statuses = suricate_workflow_steps.get(self.instance.status.identifier, [self.instance.status.identifier])
                    self.fields["status"].empty_label = None
                    self.fields["status"].queryset = ReportStatus.objects.filter(identifier__in=next_statuses)
                    # assigned_user
                    if self.old_status.identifier not in ['filed']:
                        self.fields["assigned_user"].widget = HiddenInput()
                    # message for sentinel
                    self.fields["message_sentinel"] = CharField(required=False, widget=Textarea())
                    self.fields["message_sentinel"].label = _("Message for sentinel")
                    right_after_status_index = self.fieldslayout[0].fields.index('status') + 1
                    self.fields['message_sentinel_predefined'] = forms.ModelChoiceField(
                        label=_("Predefined email"),
                        queryset=PredefinedEmail.objects.all(),
                        required=False,
                        initial=None
                    )
                    self.fieldslayout[0].insert(right_after_status_index, 'message_sentinel')
                    self.fieldslayout[0].insert(right_after_status_index, 'message_sentinel_predefined')
                    # message for supervisor
                    self.fields["message_supervisor"] = CharField(required=False, widget=Textarea())
                    self.fields["message_supervisor"].label = _("Message for supervisor")
                    right_after_user_index = self.fieldslayout[0].fields.index('assigned_user') + 1
                    self.fieldslayout[0].insert(right_after_user_index, 'message_supervisor')
                    # message for administrators
                    self.fields["message_administrators"] = CharField(required=False, widget=Textarea())
                    self.fields["message_administrators"].label = _("Message for administrators")
                    right_after_message_sentinel_index = self.fieldslayout[0].fields.index('message_sentinel') + 1
                    self.fieldslayout[0].insert(right_after_message_sentinel_index, 'message_administrators')
                    self.fields["assigned_user"].empty_label = None
                    if settings.SURICATE_WORKFLOW_SETTINGS.get("SKIP_MANAGER_MODERATION"):
                        self.fields['assigned_user'].widget = HiddenInput()
            else:
                # On new reports
                self.fields["status"].widget = HiddenInput()
                self.fields["email"].required = True
                self.fields["comment"].required = True
                self.fields["activity"].required = True
                self.fields["category"].required = True
                self.fields["problem_magnitude"].required = True
                if settings.SURICATE_WORKFLOW_ENABLED:
                    self.old_status = None
                    self.old_supervisor = None
                    self.fields["assigned_user"].widget = HiddenInput()
                    self.fields["uses_timers"].widget = HiddenInput()

    def save(self, *args, **kwargs):
        creation = not self.instance.pk
        report = super().save(self, *args, **kwargs)
        if (not creation) and settings.SURICATE_WORKFLOW_ENABLED:
            waiting_status = ReportStatus.objects.get(identifier='waiting')
            # Assign report through moderation step
            if self.old_status.identifier in ['filed'] and report.assigned_user and report.assigned_user != WorkflowManager.objects.first().user:
                msg = self.cleaned_data.get('message_supervisor', "")
                report.notify_assigned_user(msg)
                report.status = waiting_status
                report.save()
                report.lock_in_suricate()
                TimerEvent.objects.create(step=waiting_status, report=report)
            # Self-assign report without moderation step
            elif self.old_status.identifier in ['filed'] and not report.assigned_user and report.status.identifier in ['waiting']:
                report.assigned_user = self.user
                report.save()
                TimerEvent.objects.create(step=waiting_status, report=report)
            if self.old_status.identifier != report.status.identifier or self.old_supervisor != report.assigned_user:
                msg_sentinel = self.cleaned_data.get('message_sentinel', "")
                msg_admins = self.cleaned_data.get('message_administrators', "")
                report.send_notifications_on_status_change(self.old_status.identifier, msg_sentinel, msg_admins)
            if self.old_status.identifier != report.status.identifier and report.status.identifier in ['classified', 'rejected']:
                report.unlock_in_suricate()
            if 'geom' in self.changed_data and report.status.identifier in ['filed', 'waiting', 'programmed', 'late_intervention', 'late_resolution', 'solved_intervention']:  # geom cannot change for statuses 'rejected', 'classified' or 'solved'
                force_gps = False
                if self.old_status.identifier == 'filed' and report.status.identifier == 'filed' and not WorkflowDistrict.objects.filter(district__geom__covers=report.geom):
                    # from 'filed' to 'filed': set to 'waiting' in suricate
                    # Status needs to be 'waiting' for position to change in Suricate
                    relocated_message = settings.SURICATE_WORKFLOW_SETTINGS.get("SURICATE_RELOCATED_REPORT_MESSAGE")
                    report.update_status_in_suricate("waiting", relocated_message)
                    rejected_status = ReportStatus.objects.get(identifier='rejected')
                    report.status = rejected_status
                    report.save()
                    # 'force' argument needs to be passed to relocate outside of workflow district
                    force_gps = True
                # from 'filed' to 'waiting' : status was already set to be "waiting" in Suricate thanks to code above line 126
                # statuses from 'waiting' al the way through 'solved'  : status was already set to be "waiting" in Suricate thanks to previous workflow steps
                report.change_position_in_suricate(force=force_gps)
        elif report.status and report.uses_timers and (creation or self.old_status != report.status):  # Outside of workflow, create timer if report is new or if its status changed
            TimerEvent.objects.create(step=report.status, report=report)

        return report
