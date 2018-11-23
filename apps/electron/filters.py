import django_filters

from .models import Electron


class ElectronFilter(django_filters.rest_framework.FilterSet):
    model_name = django_filters.CharFilter(name="model_name", lookup_expr="icontains")
    source_web = django_filters.CharFilter(name="source_web", lookup_expr="icontains")
    factory = django_filters.CharFilter(name="factory", lookup_expr="icontains")
    class Meta:
        model = Electron
        fields = ["model_name", "source_web", "factory", "category"]
