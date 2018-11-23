from rest_framework import serializers

from ..models import Product, ProductVideo, ProductElectron, CustomProduct
from apps.electron.models import UniversalComment, Electron
from apps.scheme.models import Scheme
from apps.users.models import User


# --------------------用户界面serializers--------------------

class ElectronSerializers(serializers.ModelSerializer):
    """electron(元器件)-serializers"""

    class Meta:
        model = Electron
        fields = ['id', "model_name"]


class SchemeSerializers(serializers.ModelSerializer):
    """scheme(方案)-serializers"""

    class Meta:
        model = Scheme
        fields = ["id", "title"]


class IndexProductRecommendSerializers(serializers.ModelSerializer):
    """首页智能推荐:推荐成品-serializers"""

    class Meta:
        model = Product
        fields = ["id", "name", "views", "category"]


class IndexElectronRecommendSerializers(serializers.ModelSerializer):
    """首页智能推荐:推荐元器件-serializers"""

    class Meta:
        model = Electron
        fields = ["id", "model_name", "views", "category"]


class IndexSchemeRecommendSerializers(serializers.ModelSerializer):
    """首页智能推荐:推荐方案-serializers"""

    class Meta:
        model = Scheme
        fields = ["id", "title", "views", "category"]


class ProductVideoHomeListSerializers(serializers.ModelSerializer):
    """用户界面:成品详情- (视频列表)-serializers"""

    class Meta:
        model = ProductVideo
        exclude = ['product']


class ProductSchemeHomeListSerializers(serializers.ModelSerializer):
    """用户界面:成品详情- (方案列表)-serializers"""

    class Meta:
        model = Scheme
        fields = ['id', 'title', "category", "desc_specific", "tags", "views"]


class ElectronHomeListSerializers(serializers.ModelSerializer):
    """用户界面:核心器件-electron-serializers"""

    class Meta:
        model = Electron
        fields = ['id', 'name', "model_name"]


class ProductElectronHomeListSerializers(serializers.ModelSerializer):
    """用户界面:成品详情- (元器件列表)-serializers"""
    model_name = ElectronSerializers()

    class Meta:
        model = ProductElectron
        fields = ['model_name']


class ProductDetailHomeSerializers(serializers.ModelSerializer):
    """用户界面:成品详情-serializers"""
    videos = ProductVideoHomeListSerializers(many=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "category", "images", "videos", "factory", "desc"]


class ProductDescHomeSerializers(serializers.ModelSerializer):
    """用户界面:成品-成品介绍-serializers"""

    class Meta:
        model = Product
        fields = ["desc"]


class ProductSchemeHomeSerializers(serializers.ModelSerializer):
    """用户界面:成品-方案拆解-serializers"""
    scheme = ProductSchemeHomeListSerializers(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["scheme"]


class SimilarProductHomeSerializer(serializers.ModelSerializer):
    """用户界面:成品-同类成品推荐-serializers"""
    class Meta:
        model = Product
        fields = ["id", "name", "price", "images"]


class ProductElectronHomeDetailSerializers(serializers.ModelSerializer):
    """用户界面:成品-核心器件-serializers"""
    id = serializers.IntegerField(read_only=True)
    count = serializers.CharField(read_only=True)
    model_name = serializers.CharField(read_only=True)

    class Meta:
        model = ProductElectron
        exclude = ['create_at', 'update_at', 'product', 'model_desc']


class CustomProductHomeRetrieveSerializer(serializers.ModelSerializer):
    """用户界面:成品个性化定制-方案,元器件选择列表-serializers"""
    electrons = ProductElectronHomeListSerializers(many=True, read_only=True)
    scheme = SchemeSerializers(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["electrons", "scheme"]


class CustomProductElectronSelectSerializers(serializers.ModelSerializer):
    """用户界面:成品个性化定制-元器件选择列表-serializers"""
    electrons = ProductElectronHomeListSerializers(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["electrons"]


class CustomProductSchemeSelectSerializers(serializers.ModelSerializer):
    """用户界面:成品个性化定制-方案选择列表-serializers"""
    scheme = SchemeSerializers(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["scheme"]


class CustomProductHomeCreateSerializer(serializers.ModelSerializer):
    """用户界面:成品个性化定制-个性化定制提交-serializers"""
    electron_id = serializers.ListField(label="元器件ID", child=serializers.IntegerField())
    scheme_id = serializers.ListField(label="方案ID", child=serializers.IntegerField())

    consumer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = CustomProduct
        exclude = ['create_at', 'product', "update_at"]


class CustomProductUserSerializer(serializers.ModelSerializer):
    """用户界面:成品个性化定制-个性化定制提交数据完善-serializers"""

    class Meta:
        model = User
        fields = ["rel_name"]


class CommentUserSerializer(serializers.ModelSerializer):
    """用户界面:评论用户信息-serializers"""

    class Meta:
        model = User
        fields = ["id", "icon", "username"]


class CommentListSerializer(serializers.ModelSerializer):
    """用户界面:成品用户评论列表-serializers"""
    consumer = CommentUserSerializer()
    create_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = UniversalComment
        fields = '__all__'


class CommentCreateSerializer(serializers.ModelSerializer):
    """用户界面:成品用户评论提交-serializers"""
    consumer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    create_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = UniversalComment
        fields = ["consumer", "content", "create_at"]

