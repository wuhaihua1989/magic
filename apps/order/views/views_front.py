import os
from rest_framework.views import APIView
from rest_framework import viewsets, mixins
from rest_framework.decorators import permission_classes
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_redis import get_redis_connection
from rest_framework.decorators import action
from django.conf import settings
from apps.electron.models import Electron
from apps.order.serializer.serializers_front import *
# from apps.order.serializer.serializers_back import *
from rest_framework import status
from rest_framework import viewsets, mixins, generics
from wechatpy.pay import WeChatPay
from django_filters.rest_framework import DjangoFilterBackend
from apps.order.pagination import OrderPagination
from apps.order.filters import OrderFilter
from rest_framework import filters
import qrcode
from django.utils.six import BytesIO
from django.http.response import HttpResponse


class OrderSettlementView(APIView):
    """
    订单商品
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取当前登陆用户
        user = request.user
        print(user.username)
        # 从redis中提取购物车数据
        redis_conn = get_redis_connection('carts')
        # hgetall　获取redis中指定hash数据的所有键和值
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart = {}
        queryset = []
        for electron_id, count in redis_cart.items():
            cart[int(electron_id)] = {
                "count": int(count),
            }
        electrons = Electron.objects.filter(id__in=cart.keys())
        total_price = Decimal(0)
        for electron in electrons:
            electron.count = cart[electron.id]['count']
            electron.amount = int(electron.count) * electron.platform_price
            subtotal = electron.platform_price * electron.count
            electron_data = {
                'id': electron.id,
                'count': electron.count,
                'model_name': electron.model_name,
                # 'images': electron.images,
                'platform_price': electron.platform_price,
                'factory': electron.factory,
                'subtotal': subtotal,
            }
            total_price = total_price + subtotal
            queryset.append(electron_data)
        try:
            address = Address.objects.get(consumer__username=user.username, is_default=True)
        except Exception as e:
            freight = Decimal(0)
            serializer = OrderSettlementSerializer(
                {'freight': freight, 'electrons': queryset, 'total_price': total_price})
            return Response(serializer.data)
        freight_carrier = FreightCarrier.objects.get(id=1)
        if address.province == '广东省':
            freight = freight_carrier.gd_freight
        else:
            freight = freight_carrier.another_freight
        if total_price >= freight_carrier.max_money:
            freight = Decimal(0)
        serializer = OrderSettlementSerializer({'freight': freight, 'electrons': queryset, 'total_price': total_price})
        print(serializer.data)
        return Response(serializer.data)


class PersonReceipt(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = self.request.user
        user = User.objects.get(id=user_id.id)
        dict = {
            'rel_name': user.rel_name
        }
        return Response(dict)


class ComepanyReceipt(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = self.request.user
        user = User.objects.get(id=user_id.id)
        dict = {
            'company_name': user.company_name,
            'company_tax_number': user.company_tax_number
        }
        return Response(dict)


class SaveOrderView(CreateAPIView):
    """订单保存"""
    permission_classes = [IsAuthenticated]
    serializer_class = SaveOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        order_id = serializer.data['order_id']
        order = OrderInfo.objects.get(order_id=order_id)
        data = {'order_id': order_id, 'total_amount': order.total_amount}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


# 订单信息
class OrderInfoViewset(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = OrderInfo.objects.all()
    # serializer_class = FrontOrderInfoSerializer
    pagination_class = OrderPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_class = OrderFilter

    def get_queryset(self):
        queryset = OrderInfo.objects.filter(user=self.request.user).order_by('-create_at')
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FrontOrderDetailInfoSerializer

        return FrontOrderInfoSerializer

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.receive_goods = True
            instance.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
            instance.save()

            return Response({}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response()

    @action(['put'], detail=True)
    def remove(self, request, *args, **kwargs):
        order_id = self.kwargs['pk']
        order = OrderInfo.objects.get(order_id=order_id)
        order.status = OrderInfo.ORDER_STATUS_ENUM['CLOSED']
        order.save()
        return Response()


class PaymentView(APIView):
    """微信支付"""

    # permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        # user = request.user
        # order_id = self.request.query_params['order_id']

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          # user=user,
                                          pay_method=OrderInfo.PAY_METHODS_ENUM['WEXIN'],
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)
        wechatpay = WeChatPay(
            appid=settings.APPID,
            # sub_appid=settings.sub_appid,
            api_key=settings.API_KEY,
            mch_id=settings.MCH_ID,
            mch_cert=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../keys/apiclient_cert.pem"),
            mch_key=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../keys/apiclient_key.pem"),
            timeout=300,
            # sandbox=True,
        )
        from math import floor
        total_fee = floor(order.total_amount * 100)
        from datetime import datetime, timedelta
        from wechatpy.utils import timezone
        now = datetime.fromtimestamp(time.time(), tz=timezone('Asia/Shanghai'))
        hours_later = now + timedelta(seconds=60)
        pay_data = wechatpay.order.create(
            trade_type="NATIVE",
            body='魔方智能%s' % order_id,
            total_fee=total_fee,
            notify_url='http://www.icmofang.com/#/Wechat/',
            out_trade_no=order_id,
            product_id=1,
            time_expire=hours_later
        )
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.ERROR_CORRECT_H,
            box_size=10,
            border=1,
        )
        qr.add_data(pay_data['code_url'])
        qr.make(fit=True)
        image = qr.make_image()
        out = BytesIO()
        image.save(out, format='JPEG')
        qr_image = out.getvalue()

        return HttpResponse(qr_image, content_type="images/jpg")


class WechatOrderQuery(APIView):
    """订单确认"""
    def get(self, request, order_id):
        wechatpay = WeChatPay(
            appid=settings.APPID,
            # sub_appid=settings.sub_appid,
            api_key=settings.API_KEY,
            mch_id=settings.MCH_ID,
            mch_cert=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../keys/apiclient_cert.pem"),
            mch_key=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../keys/apiclient_key.pem"),
            timeout=300,
            # sandbox=True,
        )
        pay_data = wechatpay.order.query(out_trade_no=order_id)
        print(pay_data['trade_state'])
        if pay_data['trade_state'] == 'SUCCESS':
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            return Response({'message': '支付成功',"order_id":order_id}, status=status.HTTP_200_OK)
        elif pay_data['trade_state'] == 'NOPAY':
            return Response({'message': '未支付',}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': '其他错误',}, status=status.HTTP_204_NO_CONTENT)
