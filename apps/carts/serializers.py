from rest_framework.exceptions import APIException, _get_error_details
from rest_framework import serializers
from rest_framework import status

from apps.electron.models import Electron
from django.utils.translation import ugettext_lazy as _


class ValidationError(APIException):
    """
    重写异常类
    """
    status_code = status.status = status.HTTP_200_OK
    default_detail = _('Invalid input.')
    default_code = 'invalid'

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        # For validation failures, we may collect many errors together,
        # so the details should always be coerced to a list if not already.
        if not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]

        self.detail = _get_error_details(detail, code)


class CartSerializer(serializers.Serializer):
    """
    购物车数据序列化器
    """
    electron_id = serializers.IntegerField(label='electron id ', required=True, min_value=1)
    count = serializers.IntegerField(label='数量', required=True, min_value=1)

    def validate(self, data):
        try:
            electron = Electron.objects.get(id=data['electron_id'])
        except Electron.DoesNotExist:
            raise ValidationError({"status": 400, "message": '产品不存在'})

        # 防止出现超卖
        if data['count'] > electron.platform_stock:
            raise ValidationError({"status": 400, "message": '产品库存不足'})
        return data


class CartElectronSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = Electron
        fields = ('id', 'count', 'model_name', 'images', 'platform_price', 'factory')


class CartDeleteSerializer(serializers.Serializer):
    electron_id = serializers.IntegerField(label='electron id ', required=True, min_value=1)

    def validate_electron_id(self, value):
        try:
            electron = Electron.objects.get(id=value)
        except Electron.DoesNotExist:
            raise serializers.ValidationError({"message": '产品不存在'})

        return value
