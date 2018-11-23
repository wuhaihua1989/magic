from rest_framework import serializers
from apps.electron.models import Electron
from apps.electron.serializer.serializers_back import ElectronDetailSerializer
from .models import *
from  rest_framework.validators import UniqueValidator

from apps.scheme.models import Scheme
from apps.product.models import Product


class FreightSerializer(serializers.ModelSerializer):


    class Meta:
        model = FreightCarrier
        fields = '__all__'


class WebSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebSite
        fields = '__all__'


class SEOSerializer(serializers.ModelSerializer):
    class Meta:
        model = SEO
        fields = '__all__'


class ProtocolSerializer(serializers.ModelSerializer):

    class Meta:
        model = Protocol
        fields = '__all__'


class HotModelSerialier(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = ['id', 'model_name']


# 分类

class ContentCategorySerializer3(serializers.ModelSerializer):

    class Meta:
        model = MagicContentCategory
        fields = '__all__'


class ContentCategorySerializer2(serializers.ModelSerializer):
    children = ContentCategorySerializer3(many=True,read_only=True)

    class Meta:
        model = MagicContentCategory
        fields = '__all__'


class ContentCategorySerializer(serializers.ModelSerializer):
    children = ContentCategorySerializer2(many=True,read_only=True)

    class Meta:
        model = MagicContentCategory
        fields = '__all__'


#内容列表
class MagicContentListSerializer(serializers.ModelSerializer):

    class Meta:
        model = MagicContent
        fields = ['title', 'category','content', 'enable']

        # fields = ['title','category']

    def create(self, validated_data):

        return MagicContent.objects.create(**validated_data)


# 内容详情
class MagicContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MagicContent
        fields = '__all__'
        depth = 1


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


    # def validate(self, value):
    #
    #     # print(attrs['image'])
    #     # name = attrs['image']
    #     import filetype
    #
    #     a= filetype.guess(value)
    #     print(a)
    #     # if not str(name).endswith('.jpg'):
    #     #    return serializers.ValidationError('格式错误')
    #
    #
    #
    #     return attrs
class VedioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = '__all__'


class FilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Files
        fields = '__all__'


class HotElectronSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = ['id', 'model_name']


class HotSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['id', 'title']


class HotProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name',]


class GetHotElectronSchemeProductSerializer(serializers.Serializer):

    electron = HotElectronSerializer(many=True)
    scheme = HotSchemeSerializer(many=True)
    product =HotProductSerializer(many=True)


class LeaveMessageSerializer(serializers.ModelSerializer):
    """意见或建议"""
    class Meta:
        model = LeaveMessage
        fields = ['name', 'email', 'content']
