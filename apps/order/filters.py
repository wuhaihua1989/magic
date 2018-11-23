import django_filters
from apps.order.models import OrderInfo



# 自定义过滤类
class OrderFilter(django_filters.rest_framework.FilterSet):
    min_status = django_filters.NumberFilter(name='status',lookup_expr='gte')
    max_status = django_filters.NumberFilter(name='status',lookup_expr='lte')

    class Meta:
        model = OrderInfo
        fields = ['min_status','max_status','order_id']
