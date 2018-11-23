from rest_framework import serializers
from apps.order.models import *


class ElectronInfoserializer(serializers.ModelSerializer):
    eles = serializers.CharField(source='eles.model_name')
    factory = serializers.CharField(source='eles.factory')
    class Meta:
        model = OrderElectron
        fields = ['order', 'price', 'count', 'eles','factory']




class OrderInfoSerializer(serializers.ModelSerializer):
    eles = ElectronInfoserializer(many=True, read_only=True)
    user = serializers.CharField(source='user.username')

    class Meta:
        model = OrderInfo
        fields = ['order_id', 'total_count', 'user', 'total_amount', 'freight', 'status', 'eles', 'create_at', ]
        # fields = ('id', 'model_name', 'platform_price', 'factory', 'count')


# 快递信息序列
class CourierInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ['order_id', 'Courier_company', 'Courier_no']

class ReturnInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ['order_id', 'return_amount', 'describe']


# class UserInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['usename', 'mobile', 'default_address', 'name', 'company_name', 'company_tel_number',
#                   'company_fax_number',
#                   'company_address ', 'company_tax_number', 'bank_name', 'bank_account ', 'signer_name',
#                   'signer_mobile', 'send_address']

#
class AddressField(serializers.CharField):
    def to_representation(self, value):
        # value就是QuerySet对象列表
        address = {}
        address['address'] = value.province + value.city + value.district + value.address
        address['signer_name'] = value.signer_name
        address['signer_mobile'] = value.signer_mobile

        return address


class OrderDetailInfoSerializer(serializers.ModelSerializer):
    eles = ElectronInfoserializer(many=True, read_only=True)
    user = serializers.CharField(source='user.username')
    address = AddressField()
    # Courier_time = serializers.CharField()
    class Meta:
        model = OrderInfo
        # fields = ['order_id','total_count','user','total_amount','freight','status','eles','create_at','address']
        exclude = ['update_at']

    # def get_Courier_time(self,obj):
    #
    #     obj.Courier_time.str

