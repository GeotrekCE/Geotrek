from rest_framework import permissions as rest_permissions
from rest_framework import viewsets

from django.urls import reverse_lazy
from django.db.models import Q
from django.views.generic import CreateView, UpdateView, DetailView

from ..common.mixins.views import MetaMixin
from geotrek.flatpages.serializers import FlatPageSerializer
from geotrek.flatpages import models as flatpages_models

from .forms import FlatPageForm


class FlatPageViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing flat pages instances.
    """
    model = flatpages_models.FlatPage
    serializer_class = FlatPageSerializer
    permission_classes = [rest_permissions.DjangoModelPermissionsOrAnonReadOnly]

    def get_queryset(self):
        qs = flatpages_models.FlatPage.objects.filter(published=True)

        if self.request.GET.get('source', '') != '':
            qs = qs.filter(source__name__in=self.request.GET['source'].split(','))

        if self.request.GET.get('portal', '') != '':
            qs = qs.filter(Q(portal__name=self.request.GET['portal']) | Q(portal=None))

        return qs


class FlatPageEditMixin:
    model = flatpages_models.FlatPage
    form_class = FlatPageForm
    success_url = reverse_lazy('admin:flatpages_flatpage_changelist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class FlatPageCreate(FlatPageEditMixin, CreateView):
    pass


class FlatPageUpdate(FlatPageEditMixin, UpdateView):
    pass


class FlatPageMeta(MetaMixin, DetailView):
    model = flatpages_models.FlatPage
    template_name = 'flatpages/flatpage_meta.html'
