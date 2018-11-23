from rest_framework import serializers
from datetime import datetime
from apps.product.serializer.serializers_back import ProductListSerializers
from apps.scheme.models import *
from apps.electron.models import *
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status


class SchemeElectronSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = ['id','model_name']

class NewSchemeElectronSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeElectron
        fields = ['id', 'model_name']

# 方案类型序列化（三级目录）
class NewSchemeCategorySerializer3(serializers.ModelSerializer):
    """三级分类"""
    class Meta:
        model = SchemeCategory
        fields = '__all__'


# 方案类型序列化（二级目录）
class NewSchemeCategorySerializer2(serializers.ModelSerializer):
    """二级分类"""
    children = NewSchemeCategorySerializer3(many=True)

    class Meta:
        model = SchemeCategory
        fields = '__all__'


# 方案类型序列化（一级目录）
class NewSchemeCategoryListSerializer(serializers.ModelSerializer):
    """一级分类"""
    children = NewSchemeCategorySerializer2(many=True)

    class Meta:
        model = SchemeCategory
        fields = '__all__'


class NewSchemeDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeDocuments
        fields = '__all__'
class NewSchemeSystemDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeSystemDesign
        fields = '__all__'


class NewSchemeBomListSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model_name.model_name')
    class Meta:
        model = SchemeElectron
        exclude = ['is_record', 'create_at']

class NewSchemeVideoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeVideo
        exclude = ['scheme', 'create_at']

# 新建方案序列化
class NewSchemeSerializer(serializers.ModelSerializer):
    # scheme_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    videos = serializers.ListField(child=serializers.DictField())
    designs = serializers.ListField(child=serializers.DictField())
    electrons = serializers.ListField(child=serializers.DictField())
    category = serializers.ListField()

    class Meta:
        model = Scheme
        # fields = '__all__'
        fields = ['title', 'price','category','images','code_name', 'desc_specific','images',
                'source_code','electrons','videos','designs','contact_name','contact_tel','enterprise','contact_qq','contact_email' ]

    def validate(self, data):

        electrons = data['electrons']
        for electron in electrons:
            name = electron['model_name']
            scheme_electron = Electron.objects.get(model_name=name)
            if not scheme_electron:
                return serializers.ValidationError('%s元器件未收录'%name)
        return data

    def create(self, validated_data):
        title = validated_data['title']
        price = validated_data['price']
        category = validated_data['category'][len(validated_data['category'])-1]
        images = validated_data['images']
        videos = validated_data['videos']
        designs = validated_data['designs']
        electrons = validated_data['electrons']
        desc_specific = validated_data['desc_specific']
        code_name = validated_data['code_name']
        source_code = validated_data['source_code']
        contact_name = validated_data['contact_name']
        contact_tel = validated_data['contact_tel']
        enterprise = validated_data['enterprise']
        contact_qq = validated_data['contact_qq']
        contact_email = validated_data['contact_email']
        user = self.context["request"].user

        with transaction.atomic():
            save_id = transaction.savepoint()
            category = SchemeCategory.objects.get(id=category)
            scheme = Scheme.objects.create(
                title=title,
                scheme_user=user,
                price=price,
                category=category,
                images=images,
                desc_specific=desc_specific,
                code_name =code_name,
                source_code=source_code,
                contact_name=contact_name,
                contact_tel=contact_tel,
                enterprise=enterprise,
                contact_qq=contact_qq,
                contact_email=contact_email,
                download_count=0,
            )
            if not scheme:
                transaction.savepoint_rollback(save_id)
                raise serializers.ValidationError({"message": "方案添加失败"})

            if videos:
                for video in videos:
                    scheme_video = SchemeVideo.objects.create(
                        scheme=scheme,
                        url=video['url'],
                        is_primary=video['is_primary'],
                        create_at=datetime.now(),
                    )
                    if not scheme_video :
                        transaction.savepoint_rollback(save_id)
                        raise serializers.ValidationError({"message": "方案添加失败"})

            if designs:
                for design in designs:
                    scheme_design = SchemeSystemDesign.objects.create(
                        scheme=scheme,
                        name=design['name'],
                        image=design['image'],
                        download_count =0,

                    )
                    if not scheme_design :
                        transaction.savepoint_rollback(save_id)
                        raise serializers.ValidationError({"message": "方案添加失败"})
            if electrons:
                for electron in electrons:
                    model_name = Electron.objects.get(model_name=electron['model_name'])
                    scheme_ele  = SchemeElectron.objects.create(
                        scheme=scheme,
                        model_name=model_name,
                        model_des=electron['model_des'],
                        is_key=electron['is_key'],
                        is_record=True,
                        create_at=datetime.now()
                    )
                    if not scheme_ele:
                        transaction.savepoint_rollback(save_id)
                        raise serializers.ValidationError({"message": "方案添加失败"})

            transaction.savepoint_commit(save_id)
        print (validated_data)
        return validated_data

class NewSchemeDetailSerializer(serializers.ModelSerializer):
    videos = NewSchemeVideoListSerializer(many=True, )
    electrons = NewSchemeBomListSerializer(many=True, )
    designs = NewSchemeSystemDesignSerializer(many=True, )
    category = serializers.SerializerMethodField()

    class Meta:
        model = Scheme
        # fields = ['title', 'price','category','images','code_name', 'desc_specific','images',
        #         'source_code','electrons','videos','designs','create_at']
        fields = ['id','title', 'price', 'category', 'images', 'code_name', 'desc_specific', 'images',
                  'source_code', 'electrons', 'videos', 'designs', 'contact_name', 'contact_tel', 'enterprise',
                  'contact_qq', 'contact_email','create_at']
        # depth = 1
    def get_category(self,obj):

        category_list = []
        category = SchemeCategory.objects.get(name = obj.category)
        if category.parent:
            category_list.append(category.parent.id)
            if category.parent.parent:
                category_list.insert(0,category.parent.parent.id)
        category_list.append(category.id)
        return category_list

class NewSchemeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['id', 'title','create_at']


class SchemeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scheme
        fields = '__all__'

class ReferenceSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['id','title','images']
# class SchemeMasterSerializer(serializers.ModelSerializer):
# """方案大师"""

#     class Meta:
#         model = Scheme
#         fields = ['id', 'contact_name', 'contact_tel', 'contact_qq']

class ElectronsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Electron
        fields= '__all__'

class ElectronSimilarSerializer(serializers.ModelSerializer):

    class Meta:
        model = SimilarElectron
        fields = '__all__'

class SchemeVideoListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchemeVideo
        exclude = ['scheme', 'create_at']

# 可替换方案列表
class SimilarSchemeListSerializer(serializers.ModelSerializer):
    # similar_schemes = SimilarSchemeSerializer()

    class Meta:
        model = Scheme
        fields = ['id', 'title','images','category','is_reference', 'source_web', 'create_at',]

    # 可替代方案
class SimilarSchemeSerializer(serializers.ModelSerializer):
    similar = SimilarSchemeListSerializer()


    class Meta:
        model = SimilarScheme
        exclude = ['id','scheme','create_at']



# 方案Bom清单
class SchemeBomListSerializer(serializers.ModelSerializer):

    # name = serializers.CharField(source='model_name.model_name')
    count = serializers.CharField(read_only=True)
    model_name = serializers.ListField(child=serializers.CharField(max_length=1000,),read_only=True)


    class Meta:
        model = SchemeElectron
        fields = ['model_name','is_key','count']


# 重写CharField的to_representation方法，这个方法就是用来显示最终数据的
class MyCharField(serializers.CharField):
    def to_representation(self, value):
        # value就是QuerySet对象列表
        data_dict = {}

        a = Electron.objects.get(model_name=value)
        data_dict['id'] = a.id
        data_dict['model_name']= a.model_name
        data_dict['name']= a.name
        return data_dict

class SimilarBomSerializers(serializers.ModelSerializer):

    count = serializers.CharField(read_only=True)
    # model_name = serializers.CharField(source='model_name.model_name')
    model_name =  MyCharField(source='model_name.model_name')
    class Meta:
        model = SchemeElectron
        exclude = ['scheme','create_at']
        # depth =1

class FrontSchemeDesignSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeSystemDesign
        exclude = ['scheme']

class SchemeDownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['id','source_code','download_count']
        # fields = '__all__'



class SchemeDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeDocuments
        fields = '__all__'
from apps.product.models import Product
class FrontProductListSerializers(serializers.ModelSerializer):
    """成品列表序列化"""
    class Meta:
        model = Product
        fields = ['id', 'name', 'images','source_web', 'create_at']


class SchemeDetailPageSerializer(serializers.ModelSerializer):
    videos = SchemeVideoListSerializer(many=True, read_only=True)
    electrons = serializers.SerializerMethodField()
    # electrons = serializers.ListField(child=serializers.CharField(max_length=1000,),read_only=True)
    products =  FrontProductListSerializers(many=True, read_only=True)
    # documents = SchemeDocumentsSerializer(many=True, read_only=True)

    class Meta:
        model = Scheme
        fields = ['id','title','price','code_name','desc_specific','describe','images','download_count','source_web','electrons','videos','products']

    def get_electrons(self, obj):
        electrons = SchemeElectron.objects.filter(scheme=obj,model_name__isDelete=False).order_by('-is_key')
        for electron in electrons:
            a = SimilarElectron.objects.filter(electron=electron.model_name,similar__isDelete=False)
            b= PinToPin.objects.filter(electron=electron.model_name,pin_to_pin__isDelete=False)
            count = a.count()+b.count()
            electron.count = count
        serializer = SimilarBomSerializers(electrons,many=True)
        return serializer.data

    # def get_electrons(self, obj):
    #     electrons = SchemeElectron.objects.filter(scheme=obj).order_by('-is_key')
    #     queryset =[]
    #     for electron in electrons:
    #         dict = {}
    #         a = SimilarElectron.objects.filter(electron=electron.id)
    #         dict['count'] = a.count()
    #
    #         # queryset.append(count)
    #         dict1={
    #             'model_name':electron.model_name,
    #
    #         }
    #         dict['model_name'] = dict1
    #         queryset.append(dict)
    #     # serializer = SchemeBomListSerializer(queryset,many=True)
    #     return {'electrons':queryset}
class SearchSimilarSchemeSerializer(serializers.ModelSerializer):
    similar = SimilarSchemeListSerializer()
    class Meta:
        model = SimilarScheme
        # fields ='__all__'
        exclude = ['id','scheme','create_at']



class SchemeProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['id','name','images','market_date_at','origin']



class ElectronSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electron
        fields = ['id','model_name','platform_price','images','market_date_at']

class SchemeIncludeElectronSerializer(serializers.ModelSerializer):
    model_name = ElectronSerializer()

    class Meta:
        model = SchemeElectron
        fields = ['model_name']

class IndexSchemeSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scheme
        fields = ['id','title']