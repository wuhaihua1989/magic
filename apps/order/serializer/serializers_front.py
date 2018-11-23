from rest_framework import serializers
from django.utils import timezone
from django_redis import get_redis_connection
from django.db import transaction
from apps.config.models import FreightCarrier
from apps.electron.models import Electron
from apps.users.models import User
from apps.order.models import OrderInfo, OrderElectron
from decimal import Decimal
from django_redis import get_redis_connection
from apps.users.models import Address


class Cartserializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')
    subtotal = serializers.DecimalField(label='小计', max_digits=10, decimal_places=2)

    class Meta:
        model = Electron
        fields = ('id', 'model_name', 'platform_price', 'factory', 'count', 'subtotal')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """

    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(label='总价', max_digits=10, decimal_places=2)
    electrons = Cartserializer(many=True, read_only=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method', 'receipt', 'rel_name', 'company_name', 'company_tax_number',)
        # 设置order_id为只读字段
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        print(validated_data)
        # 获取收货地址和支付方式
        address = validated_data['address']
        pay_method = validated_data['pay_method']
        receipt = validated_data['receipt']

        rel_name = validated_data['rel_name']
        company_name = validated_data['company_name']
        company_tax_number = validated_data['company_tax_number']

        # 获取当前下单用户
        user = self.context["request"].user
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        with transaction.atomic():
            save_id = transaction.savepoint()
            # 创建订单信息
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=0,  # 订单商品总数
                total_amount=Decimal(0),  # 订单商品总金额
                freight=Decimal(0),
                pay_method=pay_method,
                status=status,
                receipt=receipt,
                rel_name=rel_name,
                company_name=company_name,
                company_tax_number=company_tax_number

            )

            redis_conn = get_redis_connection('carts')
            # hgetall　获取redis中指定hash数据的所有键和值
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            cart = {}

            for electron_id, count in redis_cart.items():
                cart[int(electron_id)] = {
                    "count": int(count),
                }
            electrons = Electron.objects.filter(id__in=cart.keys())
            total_price = Decimal(0)
            total_count = 0
            for electron in electrons:
                sku = Electron.objects.get(id=electron.id)
                electron.count = cart[electron.id]['count']
                while True:
                    origin_stock = sku.platform_stock
                    if electron.count > origin_stock:
                        transaction.savepoint_rollback(save_id)
                        raise serializers.ValidationError({"message": "商品库存不足"})
                    new_stock = origin_stock - electron.count
                    ret = Electron.objects.filter(
                        id=sku.id,
                        platform_stock=origin_stock  # 数据库的库存变成10, 还在认为是15
                    ).update(
                        platform_stock=new_stock,
                    )

                    if ret == 0:  # 如果不能更新，则表示库存发生变化，让程序再次检查库存
                        continue
                    else:
                        break  # 如果能更新，则跳出循环
                OrderElectron.objects.create(
                    order=order,
                    eles=sku,
                    count=electron.count,
                    price=sku.platform_price,
                )
                subtotal = electron.platform_price * electron.count
                total_price = total_price + subtotal
                total_count = total_count + electron.count

                try:
                    address = Address.objects.get(id=address)
                except Exception as e:
                    print(e)
                freight_carrier = FreightCarrier.objects.get(id=1)
                if address.province == '广东省':
                    global freight
                    freight = freight_carrier.gd_freight
                else:
                    freight = freight_carrier.another_freight
                if total_price >= freight_carrier.max_money:
                    freight = Decimal(0)
                    # 将bytes类型转换为int类型
            order.total_count = total_count
            order.total_amount = total_price + freight
            order.freight = freight
            order.save()
            # 提交事务
            transaction.savepoint_commit(save_id)
            # 在redis购物车中删除已计算商品数据
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart.keys())
            pl.execute()
            return order


class ElectronInfoserializer(serializers.ModelSerializer):
    eles = serializers.CharField(source='eles.model_name')
    factory = serializers.CharField(source='eles.factory')

    class Meta:
        model = OrderElectron
        fields = '__all__'


#
# class MyCharField(serializers.CharField):
#     def to_representation(self, value):
#         # value就是QuerySet对象列表
#         order = OrderInfo.objects.get(order_id=value)
#         status = order.get_status_display()#获取中文名
#         #
#         return status
class FrontOrderInfoSerializer(serializers.ModelSerializer):
    eles = ElectronInfoserializer(many=True, read_only=True)

    # status = MyCharField()
    class Meta:
        model = OrderInfo
        fields = ['order_id', 'total_count', 'total_amount', 'freight', 'status', 'eles', 'create_at']

        # def get_status(self, obj):
        #     order = OrderInfo.objects.get(order_id=obj)
        #     status = order.get_status_display()
        #     return status


class MyAddressField(serializers.CharField):
    def to_representation(self, value):
        # value就是QuerySet对象列表
        address = {}
        addr = Address.objects.get(id=value)
        address['address'] = addr.province + addr.city + addr.district + addr.address
        address['signer_name'] = addr.signer_name
        address['signer_mobile'] = addr.signer_mobile

        return address


import time


class FrontOrderDetailInfoSerializer(serializers.ModelSerializer):
    eles = ElectronInfoserializer(many=True, read_only=True)
    address = MyAddressField(source='address.id')
    # address = serializers.SerializerMethodField()
    Courier_time = serializers.SerializerMethodField()

    class Meta:
        model = OrderInfo
        fields = '__all__'

    def get_Courier_time(self, obj):
        if obj.Courier_time:
            Courier_time = obj.Courier_time.strftime('%Y-%m-%d %H:%M:%S')
            return Courier_time
        return obj.Courier_time


# 个人发票信息

class PersonReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'rel_name']


class ComepanyReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'company_name', 'company_tax_number']
