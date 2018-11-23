from django_filters.rest_framework import DjangoFilterBackend
from apps.order.pagination import OrderPagination

from apps.order.serializer.serializers_back import *
# from apps.order.serializer.serializers_front import *
from rest_framework import viewsets, mixins, generics
from rest_framework.viewsets import GenericViewSet
from rest_framework import filters
from apps.order.filters import OrderFilter
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from decimal import Decimal
# class AllOrderInfoViewsets(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
#                            mixins.ListModelMixin, GenericViewSet):


class AllOrderInfoViewset(mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.ListModelMixin,
                          GenericViewSet):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderDetailInfoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination
    filter_backends = (DjangoFilterBackend,filters.SearchFilter)
    filter_class = OrderFilter

    def get_queryset(self):
        queryset = OrderInfo.objects.all().order_by('-create_at')
        return queryset

    def get_serializer_class(self):
        # if action == 'update':
        #     return CourierInfoSerializer
        # elif action == 'returned':
        #     return ReturnInfoSerializer
        if self.action=='list':
            return OrderInfoSerializer
        else:
            return OrderDetailInfoSerializer # OrderDetailInfoSerializer

    def update(self, request, *args, **kwargs):
        try:
            data = request.data
            order_id = self.kwargs['pk']
            instance = self.get_object()
            instance.Courier_company= data['Courier_company']
            instance.Courier_no = data['Courier_no']
            instance.Courier_time = datetime.now()
            instance.save()
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['UNRECEIVED'])
            return Response()
        except Exception as e:
            return Response()

    @action(['put'],detail=True)
    def returned(self,request, *args, **kwargs):
        try:
            data = request.data
            print(data)
            order_id = self.kwargs['pk']
            instance = self.get_object()
            instance.return_amount= Decimal(data['return_amount'])
            instance.describe = data['describe']
            instance.save()
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['RETURNED'])
            return Response()
        except Exception as e:
            return Response()

