import django_filters

from .models import Product, CustomProduct


class ProductFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(name="name", lookup_expr="icontains")
    source_web = django_filters.CharFilter(name="source_web", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["name", "source_web"]


class CustomUserFilter(django_filters.rest_framework.FilterSet):
    consumer = django_filters.CharFilter(name="consumer__username", lookup_expr="icontains")

    class Meta:
        model = CustomProduct
        fields = ["consumer"]

