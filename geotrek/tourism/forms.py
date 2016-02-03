from django.utils.translation import ugettext_lazy as _

from .models import TouristicContent, TouristicEvent
from geotrek.common.forms import CommonForm


class TouristicContentForm(CommonForm):
    geomfields = ['geom']

    class Meta:
        fields = ['name', 'category', 'type1', 'type2', 'review', 'published',
                  'description_teaser', 'description', 'themes', 'contact',
                  'email', 'website', 'practical_info', 'approved', 'source',
                  'geom', 'eid', 'reservation_system', 'reservation_id', 'structure', ]
        model = TouristicContent

    def __init__(self, *args, **kwargs):
        super(TouristicContentForm, self).__init__(*args, **kwargs)
        # Since we use chosen() in trek_form.html, we don't need the default help text
        for f in ['themes', 'type1', 'type2', 'source']:
            self.fields[f].help_text = ''


class TouristicEventForm(CommonForm):
    geomfields = ['geom']

    class Meta:
        fields = ['name', 'review', 'published', 'description_teaser', 'description',
                  'themes', 'begin_date', 'end_date', 'duration',
                  'meeting_point', 'meeting_time', 'contact', 'email',
                  'website', 'organizer', 'speaker', 'type', 'accessibility',
                  'participant_number', 'booking', 'target_audience',
                  'practical_info', 'approved', 'source', 'geom', 'eid', 'structure', ]
        model = TouristicEvent

    def __init__(self, *args, **kwargs):
        super(TouristicEventForm, self).__init__(*args, **kwargs)
        self.fields['begin_date'].widget.attrs['placeholder'] = _('dd/mm/yyyy')
        self.fields['end_date'].widget.attrs['placeholder'] = _('dd/mm/yyyy')
        self.fields['meeting_time'].widget.attrs['placeholder'] = _('HH:MM')
        # Since we use chosen() in trek_form.html, we don't need the default help text
        for f in ['themes', 'source']:
            self.fields[f].help_text = ''
