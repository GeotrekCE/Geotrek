from django.core.exceptions import ValidationError
from django_filters.fields import ModelChoiceField, RangeField

from geotrek.common.widgets import OneLineRangeWidget


class ComaSeparatedMultipleModelChoiceField(ModelChoiceField):
    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            value = self.queryset.filter(**{f'{key}__in': value.split(',')})
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
        return value


class OneLineRangeField(RangeField):
    widget = OneLineRangeWidget(attrs={'class': 'minmax-field'})
