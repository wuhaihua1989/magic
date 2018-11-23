import django_filters

from .models import Scheme


class SchemeFilter(django_filters.rest_framework.FilterSet):
    title = django_filters.CharFilter(name="title", lookup_expr="icontains")
    source_web = django_filters.CharFilter(name="source_web", lookup_expr="icontains")

    class Meta:
        model = Scheme
        fields = ["title", "source_web"]


