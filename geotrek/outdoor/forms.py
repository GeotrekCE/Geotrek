from crispy_forms.layout import Div
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from geotrek.common.forms import CommonForm
from geotrek.outdoor.models import Site, Course, OrderedCourseChild


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
            'period',
            'orientation',
            'wind',
            'labels',
            'themes',
            'information_desks',
            'web_links',
            'portal',
            'source',
            'managers',
            'eid',
        )
    ]

    class Meta:
        fields = ['geom', 'structure', 'name', 'review', 'published', 'practice', 'description',
                  'description_teaser', 'ambiance', 'advice', 'period', 'labels', 'themes',
                  'portal', 'source', 'information_desks', 'web_links', 'type', 'parent', 'eid',
                  'orientation', 'wind', 'managers']
        model = Site

    def __init__(self, site=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].initial = site
        if self.instance.pk:
            descendants = self.instance.get_descendants(include_self=True).values_list('pk', flat=True)
            self.fields['parent'].queryset = Site.objects.exclude(pk__in=descendants)
        if self.instance.practice:
            for scale in self.instance.practice.rating_scales.all():
                for bound in ('max', 'min'):
                    ratings = getattr(self.instance, 'ratings_' + bound).filter(scale=scale)
                    fieldname = 'rating_scale_{}{}'.format(bound, scale.pk)
                    self.fields[fieldname] = forms.ModelChoiceField(
                        label="{} {}".format(scale.name, bound),
                        queryset=scale.ratings.all(),
                        required=False,
                        initial=ratings[0] if ratings else None
                    )
                    self.fieldslayout[0].insert(10, fieldname)

    def save(self, *args, **kwargs):
        site = super().save(self, *args, **kwargs)

        # Save ratings
        if site.practice:
            for bound in ('min', 'max'):
                field = getattr(site, 'ratings_' + bound)
                to_remove = list(field.exclude(scale__practice=site.practice).values_list('pk', flat=True))
                to_add = []
                for scale in site.practice.rating_scales.all():
                    rating = self.cleaned_data.get('rating_scale_{}{}'.format(bound, scale.pk))
                    if rating:
                        to_remove += list(field.filter(scale=scale).exclude(pk=rating.pk).values_list('pk', flat=True))
                        to_add.append(rating.pk)
                    else:
                        to_remove += list(field.filter(scale=scale).values_list('pk', flat=True))
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
            'structure',
            'name',
            'site',
            'review',
            'published',
            'description',
            'advice',
            'equipment',
            'height',
            'children_course',
            'eid',
            'hidden_ordered_children',
        )
    ]

    class Meta:
        fields = ['geom', 'structure', 'name', 'site', 'review', 'published', 'description',
                  'advice', 'equipment', 'height', 'eid', 'children_course', 'hidden_ordered_children']
        model = Course

    def __init__(self, site=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['site'].initial = site
        if self.instance.pk and self.instance.site and self.instance.site.practice:
            for scale in self.instance.site.practice.rating_scales.all():
                ratings = self.instance.ratings.filter(scale=scale)
                fieldname = 'rating_scale_{}'.format(scale.pk)
                self.fields[fieldname] = forms.ModelChoiceField(
                    label=scale.name,
                    queryset=scale.ratings.all(),
                    required=False,
                    initial=ratings[0] if ratings else None
                )
                self.fieldslayout[0].insert(5, fieldname)
        if self.instance:
            queryset_children = OrderedCourseChild.objects.filter(parent__id=self.instance.pk).order_by('order')
            # init multiple children field with data
            self.fields['children_course'].queryset = Course.objects.exclude(pk=self.instance.pk)
            self.fields['children_course'].initial = [c.child.pk for c in self.instance.course_children.all()]
            # init hidden field with children order
            self.fields['hidden_ordered_children'].initial = ",".join(str(x) for x in queryset_children.values_list('child__id', flat=True))

    def clean_children_course(self):
        """
        Check the course is not parent and child at the same time
        """
        children = self.cleaned_data['children_course']
        if children and self.instance and self.instance.course_parents.exists():
            raise ValidationError(_("Cannot add children because this course is itself a child."))
        for child in children:
            if child.course_children.exists():
                raise ValidationError(_("Cannot use parent course {name} as a child course.".format(name=child.name)))
        return children

    def save(self, *args, **kwargs):
        course = super().save(self, *args, **kwargs)

        # Save ratings
        if course.site and course.site.practice:
            to_remove = list(course.ratings.exclude(scale__practice=course.site.practice).values_list('pk', flat=True))
            to_add = []
            for scale in course.site.practice.rating_scales.all():
                rating = self.cleaned_data.get('rating_scale_{}'.format(scale.pk))
                if rating:
                    to_remove += list(course.ratings.filter(scale=scale).exclude(pk=rating.pk).values_list('pk', flat=True))
                    to_add.append(rating.pk)
                else:
                    to_remove += list(course.ratings.filter(scale=scale).values_list('pk', flat=True))
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
