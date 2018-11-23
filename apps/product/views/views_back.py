from rest_framework import viewsets, status, filters, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from apps.product.pagination import Pagination
from ..filters import ProductFilter, CustomUserFilter

from apps.electron.models import Electron
from apps.scheme.models import Scheme
from apps.product.models import ProductCategory, Product, CustomProduct

from apps.product.serializer.serializers_back import ProductCategorySerializers, ProductCategorySerializers1
from apps.product.serializer.serializers_back import ProductListSerializers, ProductDetailSerializers
from apps.product.serializer.serializers_back import ProductSchemeListSerializers, ProductElectronDetailSerializers
from apps.product.serializer.serializers_back import CustomProductListSerializers, CustomProductDetailSerializer
from apps.product.serializer.serializers_back import ProductCreateSerializers


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
        retrieve:
           产品分类详情
        list:
           产品分类列表（无子类）
        create:
           产品分类新增
        categories_list:
           产品分类列表（有子类）
        delete:
           产品分类删除
        update:
           产品分类更新
    """

    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializers

    @action(['get'], detail=False)
    def categories_list(self, request):
        product_categories = ProductCategory.objects.filter(parent=None)
        serializer = ProductCategorySerializers1(product_categories, many=True)
        if serializer.data:
            for data in serializer.data:
                if data['children']:
                    for data1 in data['children']:
                        if not data1['children']:
                            data1['children'] = None
                else:
                    data['children'] = None
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductViewSet(viewsets.ModelViewSet):
    """
    成品
        list:
            成品列表
        update:
            成品修改
        delete:
            成品删除
        retrieve:
            成品详情
        create:
            成品添加
    """
    queryset = Product.objects.all().order_by('-create_at')
    serializer_class = ProductListSerializers
    filter_backends = [DjangoFilterBackend]
    filter_class = ProductFilter
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializers
        elif self.action == 'create':
            return ProductCreateSerializers
        else:
            return ProductDetailSerializers

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        product_category = ProductCategory.objects.get(id=instance.category_id)
        category_list = []
        if product_category.parent_id:
            product_category1 = ProductCategory.objects.get(id=product_category.parent_id)
            if product_category1.parent_id:
                category_list.append(product_category1.parent_id)
                category_list.append(product_category1.id)
            else:
                category_list.append(product_category1.id)
            category_list.append(instance.category_id)
        else:
            category_list.append(instance.category_id)
        data = serializer.data
        data['category'] = category_list
        return Response(data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "添加成品成功!"}, status=status.HTTP_201_CREATED)

    # @action(['get'], detail=False)
    # def sschemes(self, request, *args, **kwargs):
    #     """成品方案搜索"""
    #     try:
    #         product = self.get_object()
    #         product_schemes = set(product.scheme.all())
    #         scheme_title = request.query_params['title']
    #         schemes = set(Scheme.objects.filter(title__istartswith=scheme_title))
    #         difference_schemes = list(schemes.difference(product_schemes))[:10]
    #         serializer = ProductSchemeListSerializers(difference_schemes, many=True)
    #         if serializer.data:
    #             return Response(serializer.data, status=status.HTTP_200_OK)
    #         else:
    #             return Response({"fail": "数据库未收录该方案", "status": 1001}, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         print(e)
    #         return Response({'error': e}, status=status.HTTP_200_OK)
    #
    # @action(['get'], detail=False)
    # def selectron(self, request, *args, **kwargs):
    #     """成品BOM器件搜索"""
    #     try:
    #         product = self.get_object()
    #         model_name = request.query_params['model_name']
    #         product_electrons = set(Electron.objects.filter(pro_electrons__product=product))
    #         electrons = set(Electron.objects.filter(model_name__istartswith=model_name))
    #         difference_electrons = list(electrons.difference(product_electrons))[:10]
    #         serializer = ProductElectronDetailSerializers(difference_electrons, many=True)
    #         if serializer.data:
    #             return Response(serializer.data, status=status.HTTP_200_OK)
    #         else:
    #             return Response({"fail": "数据库未收录该元器件", "status": 1001}, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         print(e)
    #         return Response({'error': e}, status=status.HTTP_200_OK)


class ProductSchemeSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """成品方案搜索"""
    queryset = Scheme.objects.all()
    serializer_class = ProductSchemeListSerializers

    def list(self, request, *args, **kwargs):
        scheme_title = request.query_params['title']
        queryset = Scheme.objects.filter(title__istartswith=scheme_title)[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductElectronSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """成品BOM器件搜索"""
    queryset = Electron.objects.all()
    serializer_class = ProductElectronDetailSerializers

    def list(self, request, *args, **kwargs):
        model_name = request.query_params['model_name']
        queryset = Electron.objects.filter(model_name__istartswith=model_name, isDelete=False)[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CustomProductViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    成品定制
        list:
            成品定制列表
        retrieve:
            成品定制详情
        destroy:
            成品定制删除
    """
    queryset = CustomProduct.objects.all().order_by('-create_at')
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filter_class = CustomUserFilter
    search_fields = ['consumer__username']
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == 'list':
            return CustomProductListSerializers
        else:
            return CustomProductDetailSerializer

