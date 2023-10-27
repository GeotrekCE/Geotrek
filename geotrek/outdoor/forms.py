from django.conf import settings
from crispy_forms.layout import Div
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from geotrek.common.mixins.forms import CommonForm
from geotrek.outdoor.models import RatingScale, Site, Course, OrderedCourseChild


class SiteForm(CommonForm):
    orientation = forms.MultipleChoiceField(choices=Site.ORIENTATION_CHOICES, required=False)
    wind = forms.MultipleChoiceField(choices=Site.ORIENTATION_CHOICES, required=False)

    geomfields = ['geom']

    fieldslayout = [
        Div(
            'structure',
            'name',
            'parent',
            'review',
            'published',
            'practice',
            'type',
            'description_teaser',
            'ambiance',
            'description',
            'advice',
            'accessibility',
            'period',
            'orientation',
            'wind',
            'labels',
            'themes',
            'information_desks',
            'web_links',
            'portal',
            'source',
            'pois_excluded',
            'managers',
            'eid',
        )
    ]

    class Meta:
        fields = ['geom', 'structure', 'name', 'review', 'published', 'practice', 'description',
                  'description_teaser', 'ambiance', 'advice', 'period', 'labels', 'themes',
                  'portal', 'source', 'information_desks', 'web_links', 'type', 'parent', 'accessibility', 'eid',
                  'orientation', 'wind', 'managers', 'pois_excluded']
        model = Site

    def __init__(self, site=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].initial = site
        if self.instance.pk:
            descendants = self.instance.get_descendants(include_self=True).values_list('pk', flat=True)
            self.fields['parent'].queryset = Site.objects.exclude(pk__in=descendants)
        for scale in RatingScale.objects.all():
            ratings = None
            if self.instance.pk:
                ratings = self.instance.ratings.filter(scale=scale)
            fieldname = f'rating_scale_{scale.pk}'
            self.fields[fieldname] = forms.ModelMultipleChoiceField(
                label=scale.name,
                queryset=scale.ratings.all(),
                required=False,
                initial=ratings if ratings else None
            )
            right_after_type_index = self.fieldslayout[0].fields.index('type') + 1
            self.fieldslayout[0].insert(right_after_type_index, fieldname)
        if self.instance.pk:
            self.fields['pois_excluded'].queryset = self.instance.all_pois.all()
        else:
            self.fieldslayout[0].remove('pois_excluded')

    def clean(self):
        cleaned_data = super().clean()
        practice = self.cleaned_data['practice']
        for scale in RatingScale.objects.all():
            if self.cleaned_data.get(f'rating_scale_{scale.pk}'):
                try:
                    practice.rating_scales.get(pk=scale.pk)
                except RatingScale.DoesNotExist:
                    raise ValidationError(_("One of the rating scale use is not part of the practice chosen"))
        return cleaned_data

    def save(self, *args, **kwargs):
        site = super().save(self, *args, **kwargs)

        # Save ratings
        if site.practice:
            field = getattr(site, 'ratings')
            to_remove = list(field.exclude(scale__practice=site.practice).values_list('pk', flat=True))
            to_add = []
            for scale in site.practice.rating_scales.all():
                ratings = self.cleaned_data.get(f'rating_scale_{scale.pk}')
                needs_removal = field.filter(scale=scale)
                if ratings is not None:
                    for rating in ratings:
                        needs_removal = needs_removal.exclude(pk=rating.pk)
                        to_add.append(rating.pk)
                to_remove += list(needs_removal.values_list('pk', flat=True))
            field.remove(*to_remove)
            field.add(*to_add)

        return site


class CourseForm(CommonForm):
    children_course = forms.ModelMultipleChoiceField(label=_("Children"),
                                                     queryset=Course.objects.all(), required=False,
                                                     help_text=_("Select children in order"))
    hidden_ordered_children = forms.CharField(label=_("Hidden ordered children"),
                                              widget=forms.widgets.HiddenInput(),
                                              required=False)

    geomfields = ['geom']

    fieldslayout = [
        Div(
            'points_reference',
            'structure',
            'name',
            'parent_sites',
            'type',
            'review',
            'published',
            'description',
            'ratings_description',
            'duration',
            'advice',
            'gear',
            'equipment',
            'accessibility',
            'height',
            'pois_excluded',
            'children_course',
            'eid',
            'hidden_ordered_children',
        )
    ]

    class Meta:
        fields = ['geom', 'structure', 'name', 'parent_sites', 'type', 'review', 'published', 'description', 'ratings_description', 'duration', 'pois_excluded',
                  'points_reference', 'advice', 'gear', 'equipment', 'accessibility', 'height', 'eid', 'children_course', 'hidden_ordered_children']
        model = Course

    def __init__(self, parent_sites=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_sites'].queryset = Site.objects.only('name').order_by('name')
        if parent_sites:
            self.fields['parent_sites'].initial = parent_sites
        self.fields['duration'].widget.attrs['min'] = '0'
        for scale in RatingScale.objects.all():
            ratings = None
            if self.instance.pk and self.instance.parent_sites.exists() and self.instance.parent_sites.first().practice:
                ratings = self.instance.ratings.filter(scale=scale)
            fieldname = f'rating_scale_{scale.pk}'
            self.fields[fieldname] = forms.ModelChoiceField(
                label=scale.name,
                queryset=scale.ratings.all(),
                required=False,
                initial=ratings[0] if ratings else None
            )
            right_after_type_index = self.fieldslayout[0].fields.index('type') + 1
            self.fieldslayout[0].insert(right_after_type_index, fieldname)
        if self.instance:
            queryset_children = OrderedCourseChild.objects.filter(parent__id=self.instance.pk).order_by('order')
            # init multiple children field with data
            self.fields['children_course'].queryset = Course.objects.exclude(pk=self.instance.pk)
            self.fields['children_course'].initial = [c.child.pk for c in self.instance.course_children.all()]
            # init hidden field with children order
            self.fields['hidden_ordered_children'].initial = ",".join(str(x) for x in queryset_children.values_list('child__id', flat=True))
        if self.instance.pk:
            self.fields['pois_excluded'].queryset = self.instance.all_pois.all()
        else:
            self.fieldslayout[0].remove('pois_excluded')
        if not settings.OUTDOOR_COURSE_POINTS_OF_REFERENCE_ENABLED:
            self.fields.pop('points_reference')
        else:
            # Edit points of reference with custom edition JavaScript class
            self.fields['points_reference'].label = ''
            self.fields['points_reference'].widget.target_map = 'geom'
            self.fields['points_reference'].widget.geometry_field_class = 'PointsReferenceField'

    def clean_children_course(self):
        """
        Check the course is not parent and child at the same time
        """
        children = self.cleaned_data['children_course']
        if children and self.instance and self.instance.course_parents.exists():
            raise ValidationError(_("Cannot add children because this course is itself a child."))
        for child in children:
            if child.course_children.exists():
                raise ValidationError(_(f"Cannot use parent course {child.name} as a child course."))
        return children

    def save(self, *args, **kwargs):
        course = super().save(self, *args, **kwargs)

        # Save ratings
        if course.parent_sites.exists() and course.parent_sites.first().practice:
            to_remove = list(course.ratings.exclude(scale__practice=course.parent_sites.first().practice).values_list('pk', flat=True))
            to_add = []
            for scale in course.parent_sites.first().practice.rating_scales.all():
                rating = self.cleaned_data.get(f'rating_scale_{scale.pk}')
                needs_removal = course.parent_sites.first().ratings.filter(scale=scale)
                if rating:
                    needs_removal = needs_removal.exclude(pk=rating.pk)
                    to_add.append(rating.pk)
                to_remove += list(needs_removal.values_list('pk', flat=True))
            course.ratings.remove(*to_remove)
            course.ratings.add(*to_add)

        # Save children
        ordering = []
        if self.cleaned_data['hidden_ordered_children']:
            ordering = self.cleaned_data['hidden_ordered_children'].split(',')
        order = 0
        # add and update
        for value in ordering:
            child, created = OrderedCourseChild.objects.get_or_create(parent=self.instance,
                                                                      child=Course.objects.get(pk=value))
            child.order = order
            child.save()
            order += 1
        # delete
        new_list_children = self.cleaned_data['children_course'].values_list('pk', flat=True)
        for child_relation in self.instance.course_children.all():
            # if existant child not in selection, deletion
            if child_relation.child_id not in new_list_children:
                child_relation.delete()

        return course
