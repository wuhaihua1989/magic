from django.db.models import Q
from rest_framework import serializers

from apps.electron.models import *
from apps.scheme.models import Scheme
from apps.electron.validators import ValidationError


# ---------客户端界面------------
class FelectronSupplierSerializer(serializers.ModelSerializer):

    class Meta:
            model = Supplier
            fields = '__all__'


class SupplierDetailSerializer(serializers.ModelSerializer):
    mes = FelectronSupplierSerializer(many=True, read_only=True)

    class Meta:
            model = Supplier
            fields = ['mes']


class FrontElectronSerializer(serializers.ModelSerializer):
    supplier = SupplierDetailSerializer(many=True)

    class Meta:
        model = Electron
        fields = ['supplier']


# -----------
# 产品类型序列化（三级目录）
class ElectronCategoryAllSerializer3(serializers.ModelSerializer):
    """三级分类"""

    class Meta:
        model = ElectronCategory
        fields = '__all__'


# 产品类型序列化（二级目录）
class SchemeCategorySerializer2(serializers.ModelSerializer):
    """二级分类"""
    children = ElectronCategoryAllSerializer3(many=True)

    class Meta:
        model = ElectronCategory
        fields = '__all__'


# 产品类型序列化（一级目录）
class ElectronCategoryAllSerializer(serializers.ModelSerializer):
    """一级分类"""
    children = SchemeCategorySerializer2(many=True)

    class Meta:
        model = ElectronCategory
        fields = '__all__'


# 元器件序列化
class ElectronSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = '__all__'


# 元器件列表
class ElectronBackListSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = Electron
        fields = ['id', 'model_name', 'factory', 'category', 'source_web', 'is_supply']


# 元器件表参数序列化器
class ElectronsKwargsValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronKwargsValueFront
        fields = '__all__'


# 元器件详情
class ElectronDetailSerializer(serializers.ModelSerializer):
    electron_kwargs = ElectronsKwargsValueSerializer(many=True)

    class Meta:
        model = Electron
        fields = ['id', 'category', 'model_name', 'images', 'is_supply', 'desc_specific', 'electron_kwargs', 'factory',
                  'origin', 'market_date_at', 'supplier', 'data_sheet_name', 'data_sheet', 'platform_price', 'platform_stock']


# 产品更新序列化
class ElectronRetrieveUpdateSerializer(serializers.ModelSerializer):
    electron_kwargs = serializers.ListField(child=serializers.DictField())

    class Meta:
        model = Electron

        fields = ['model_name', 'images', 'is_supply', 'desc_specific', 'electron_kwargs',
                  'origin', 'market_date_at',  'data_sheet_name', 'data_sheet', 'factory']


# 产品添加序列化
class ElectronRetrieveCreateSerializer(serializers.ModelSerializer):
    electron_kwargs = serializers.ListField(child=serializers.DictField())
    category = serializers.ListField()

    class Meta:
        model = Electron

        fields = ['category', 'model_name', 'images', 'is_supply', 'desc_specific', 'electron_kwargs',
                  'origin', 'market_date_at', 'data_sheet_name', 'data_sheet', 'platform_price', 'platform_stock', 'factory']

    def validate_category(self, category):
        if not category:
            raise ValidationError({"error_message": "产品类型不能为空!"})
        return category

    def validate_model_name(self, model_name):
        if Electron.objects.filter(model_name=model_name, isDelete=False).count():
            raise ValidationError({"error_message": "元器件已经存在!", "status": "401"})
        return model_name

    def create(self, validated_data):
        try:

            category = validated_data['category']
            electron_kwargs = validated_data['electron_kwargs']
            # 保存产品
            electron = Electron()
            electron.model_name = validated_data['model_name']
            electron.category_id = category[-1]
            electron.images = validated_data['images']
            electron.factory = validated_data['factory']
            electron.is_supply = validated_data['is_supply']
            electron.desc_specific = validated_data['desc_specific']
            electron.origin = validated_data['origin']
            electron.market_date_at = validated_data['market_date_at']
            electron.data_sheet_name = validated_data['data_sheet_name']
            electron.data_sheet = validated_data['data_sheet']
            electron.platform_price = validated_data['platform_price']
            electron.platform_stock = validated_data['platform_stock']
            electron.save()
        except Exception as e:
            raise ValidationError({"message": "保存元器件失败!", "error_message": e.args[0]})

        # 保存产品参数
        try:
            if electron_kwargs:
                for kwargs in electron_kwargs:
                    # if kwargs["kwargs_value"] != "":
                    electron_parameter = ElectronKwargsValueFront()
                    electron_parameter.electron = electron
                    electron_parameter.kwargs_name = kwargs['cname']
                    electron_parameter.kwargs_value = kwargs["kwargs_value"]
                    electron_parameter.kwargs_id = kwargs['id']
                    electron_parameter.save()
        except Exception as e:
            Electron.objects.filter(id=electron.id).delete()
            raise ValidationError({"electron": "保存元器件参数失败!", "error_message": e.args[0]})
        return electron


# 元器件分类参数列表序列化器
class ElectronsKwargsSerializer(serializers.ModelSerializer):
    kwargs_value = serializers.SerializerMethodField(label='参数值', help_text='参数值')

    def get_kwargs_value(self, obj):
        kwargs_values = ElectronKwargsValue.objects.filter(kwargs=obj)
        kwargs_value = [kwarg.value for kwarg in kwargs_values]
        kwargs_value.clear()
        return ",".join(kwargs_value)

    class Meta:
        model = ElectronKwargs
        fields = ["id", "kwargs_value", "cname"]


# 供应商添加序列化器
class ElectronCreateSupplierSerlializer(serializers.ModelSerializer):
    electron_supplier = serializers.ListField(child=serializers.DictField())

    class Meta:
        model = Supplier
        fields = ["name", "phone_number", "electron_supplier"]

    def create(self, validated_data):
        try:
            electron_supplier = validated_data['electron_supplier']

            # 保存供应商
            supplier = Supplier()
            supplier.name = validated_data['name']
            supplier.phone_number = validated_data['phone_number']
            supplier.save()
        except Exception as e:
            raise ValidationError({"fail": "添加供应商失败!", "error_message": e})

            # 保存产品供应商
        try:
            if electron_supplier:
                for suppliers in electron_supplier:
                    electron_suppliers = ElectronSupplier()
                    electron_suppliers.electron_id = suppliers['electron']
                    electron_suppliers.supplier = supplier
                    electron_suppliers.inventory = suppliers['inventory']
                    electron_suppliers.price = suppliers['price']
                    electron_suppliers.batch_no = suppliers['batch_no']
                    electron_suppliers.save()
        except Exception as e:
            Supplier.objects.filter(id=supplier.id).delete()
            raise ValidationError({"electron": "添加供应商失败!", "error_message": e.args[0]})
        return supplier


# 添加视频
class ElectronCreateVideoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronVideo
        fields = ["electron", "url", "title"]

    def create(self, validated_data):
        try:
            # 保存视频地址
            video = ElectronVideo()
            video.electron = validated_data['electron']
            video.url = validated_data['url']
            video.title = validated_data['title']
            primary_electron = ElectronVideo.objects.filter(Q(electron_id=video.electron.id) & Q(is_primary=True))
            if len(primary_electron) == 0:
                video.is_primary = True
                video.save()
            else:
                video.save()
        except Exception as e:
            raise ValidationError({"fail": "保存视频失败!", "error_message": e})
        return video


# 元器件修改
class ElectronUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = ['id', 'category', 'model_name',
                  'is_supply', 'desc_specific', 'kwargs_values', 'origin', 'market_date_at']


# 元器件应用支持
class ElectronApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = ['id', 'factory_link']


# 元器件分类（三级目录）
class ElectronCategorySerializer3(serializers.ModelSerializer):
    """三级分类"""
    class Meta:
        model = ElectronCategory
        fields = '__all__'


# 元器件分类（二级目录）
class ElectronCategorySerializer2(serializers.ModelSerializer):
    """二级分类"""
    children = ElectronCategorySerializer3(many=True)

    class Meta:
        model = ElectronCategory
        fields = '__all__'


# 元器件分类（一级目录）
class ElectronCategoryListSerializer(serializers.ModelSerializer):
    """一级分类"""
    children = ElectronCategorySerializer2(many=True)

    class Meta:
        model = ElectronCategory
        fields = '__all__'


# 元器件分类
class ElectronCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronCategory
        fields = '__all__'


# 元器件参考设计
class ElectronSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['id', 'title', 'desc_specific']


# 可替代元器件
class SimilarElectronSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimilarElectron
        fields = '__all__'


# 供应商
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


# 元器件供应商
class ElectronSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronSupplier
        fields ='__all__'


# 元器件供应商列表
class ElectronSupplierListSerializer(serializers.ModelSerializer):
    supplier = serializers.SlugRelatedField(read_only=True, slug_field='name')
    phone = serializers.SerializerMethodField()

    class Meta:
        model = ElectronSupplier
        fields = ['supplier', 'inventory', 'price', 'batch_no', 'phone', 'electron']

    def get_phone(self, obj):
        return obj.supplier.phone_number


# 元器件原理图
class ElectronCircuitDiagramSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronCircuitDiagram
        fields = '__all__'


# 元器件参数
class ElectronKwargsSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField(label='参数值', help_text='参数值', allow_null=True)

    def get_values(self, obj):
        kwargs_value = ElectronKwargsValue.objects.filter(kwargs=obj)
        values = [kwarg.value for kwarg in kwargs_value]
        return ",".join(values)

    class Meta:
        model = ElectronKwargs
        fields = '__all__'


# 元器件参数值
class ElectronKwargsValueSerializer(serializers.ModelSerializer):
    values = serializers.CharField(allow_null=True, write_only=True)

    class Meta:
        model = ElectronKwargs
        fields = ('electron', 'cname', 'ename', 'is_contrast', 'is_substitute', 'values')

    def validate(self, attrs):
        cname = attrs['cname']
        electron = attrs['electron']
        if ElectronKwargs.objects.filter(cname=cname, electron=electron).count():
            raise ValidationError({"error_message": "参数名已经存在!", "status": "401"})
        return attrs

    def create(self, validated_data):
        try:
            values = validated_data['values']
            # 保存参数名
            Kwargs = ElectronKwargs()
            Kwargs.cname = validated_data['cname']
            Kwargs.electron = validated_data['electron']
            Kwargs.ename = validated_data['ename']
            Kwargs.is_substitute = validated_data['is_substitute']
            Kwargs.is_contrast = validated_data['is_contrast']
            Kwargs.origin = validated_data['is_substitute']
            Kwargs.save()
        except Exception as e:
            raise ValidationError({"fail": "保存参数名失败!", "error_message": e})

        # 保存分类参数值
        try:
            if values:
                values = values.split(',')
                for kwargs_value in values:
                    electron_value = ElectronKwargsValue()
                    electron_value.kwargs = Kwargs
                    electron_value.value = kwargs_value
                    electron_value.save()
        except Exception as e:
            raise ValidationError({"electron": "保存参数失败!", "error_message": e.args[0]})
        return Kwargs


# 元器件参数值详情
class ElectronKVDetailSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField(label='参数值', help_text='参数值')

    def get_values(self, obj):
        kwargs_value = ElectronKwargsValue.objects.filter(kwargs=obj)
        values = [kwarg.value for kwarg in kwargs_value]
        return values

    class Meta:
        model = ElectronKwargs
        fields = '__all__'


# 元器件视频
class ElectronVideoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronVideo
        fields = '__all__'


# 元器件消费者
class ElectronConsumerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronConsumer
        fields = '__all__'


# 元器件模型
class ElectronModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = ['id', 'model_name']


# PintoPin元器件列表
class ElectronPlistSerializer(serializers.ModelSerializer):
    pin_to_pin = serializers.SlugRelatedField(read_only=True, slug_field='model_name')

    class Meta:
        model = PinToPin
        exclude = ['electron', 'create_at']


# 可替换元器件列表
class ElectronSlistSerializer(serializers.ModelSerializer):
    similar = serializers.SlugRelatedField(read_only=True, slug_field='model_name')

    class Meta:
        model = SimilarElectron
        exclude = ['electron', 'create_at']


# PinToPin 器件新增
class PinToPinCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PinToPin
        fields = '__all__'


# 评论用户
class CommentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'icon', 'rel_name']


# 数据表序列化器
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronFile
        fields = ['data_sheet_name', 'data_sheet']


# 自动匹配可替换元器件序列化器
class ElectronSimilarSerializer(serializers.ModelSerializer):
    electron_kwargs = ElectronsKwargsValueSerializer(many=True)

    class Meta:
        model = ElectronKwargs
        fields = ['id', 'electron', 'cname', 'is_contrast']

    def update(self, instance, validated_data):

        instance.model_name = validated_data['model_name']
        instance.category = validated_data['category']
        instance.cname = validated_data['cname']
        instance.value = validated_data['value']
        instance.is_contrast = validated_data['is_contrast']
        electron = Electron.objects.get(model_name=instance.model_name)







