from rest_framework import serializers

from apps.electron.models import Electron, ElectronKwargsValueFront
from apps.electron.models import ElectronSupplier
from apps.electron.models import ElectronKwargs
from apps.electron.models import ElectronCircuitDiagram
from apps.electron.models import ElectronVideo
from apps.electron.models import PinToPin
from apps.electron.models import SimilarElectron
from apps.scheme.models import SchemeElectron, Scheme, SchemeCategory
from apps.product.models import Product, ProductCategory


class ElecvideosSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronVideo
        fields = '__all__'


class ElectronKwargsValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronKwargsValueFront
        fields = '__all__'


# 产品详情
class SkuDetailSerializer(serializers.ModelSerializer):
    video_electron = ElecvideosSerializer(many=True)
    electron_kwargs = ElectronKwargsValueSerializer(many=True)

    class Meta:
        model = Electron
        fields = ['id', 'model_name', 'desc_specific', 'images', 'electron_kwargs', 'platform_price', 'specifc', 'video_electron','data_sheet', 'data_sheet_name', 'factory_link', 'factory']


# 产品供应商
class ElectronDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronSupplier
        fields = ['id', 'price', 'supplier']
        depth = 1


# 电路图
class CircuitSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronCircuitDiagram
        fields = ['id', 'name', 'diagram']


# 产品详情页视频
class ElectronDetailVideoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronVideo
        fields = ['id', 'url', 'title']


# 热销产品
class HotElectronSerializer(serializers.ModelSerializer):

    class Meta:
        model = Electron
        fields = ('id', 'model_name')


# 可替换元器件列表
class SimilarSerializer(serializers.ModelSerializer):

    class Meta:
        model = SimilarElectron
        fields = ('id', 'similar')
        depth = 2


# 首页推荐元器件
class SchemesElectronSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchemeElectron
        fields = ('model_name', 'id')


class ElectronsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Electron
        fields = ('id', 'model_name', 'images', 'factory')


class PinToPinsElectronSerializer(serializers.ModelSerializer):

    class Meta:
        model = PinToPin
        fields = ('pin_to_pin', )
        depth = 2


class SimiliarElectronSerializer(serializers.ModelSerializer):

    class Meta:
        model = SimilarElectron
        fields = ('similar', )
        depth = 2


class SearchSchemeSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.id")

    class Meta:
        model = Scheme
        fields = ["id", "title", "category", "is_reference", "images"]


# 方案序列化
class SchemesSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(label='总计', read_only=True)

    class Meta:
        model = Scheme
        fields = ('title', 'is_reference', 'count')


class ProductSerializers(serializers.ModelSerializer):
    category = serializers.CharField(source="category.id")

    class Meta:
        model = Product
        fields = ["id", "origin", "category", "market_date_at", "name", "images"]


# 搜索结果页对比序列化器
class ElectronContrastSerializer(serializers.ModelSerializer):
    # market_date_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d')

    class Meta:
        model = Electron
        fields = ('id', 'model_name', 'images', 'platform_price', 'market_date_at', 'factory')


# 对比页面序列化器
class ElectronKwargsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ElectronKwargs
        fields = '__all__'


# 搜索结果页对比序列化器
class ElectronsKwargsSerializer(serializers.ModelSerializer):
    kwargs = ElectronKwargsSerializer()

    class Meta:
        model = ElectronKwargsValueFront
        fields = ('electron', 'kwargs', 'kwargs_value')


class SchemeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeCategory
        fields = ('id', 'name')


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ('id', 'name')