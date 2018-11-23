from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import status
from rest_framework import (viewsets, generics, mixins)
from rest_framework.generics import UpdateAPIView, GenericAPIView, CreateAPIView
from rest_framework.mixins import ListModelMixin

from apps.electron.serializer.serializers_back import *
from apps.electron.pagination import *
from rest_framework.decorators import action
from django.db import transaction
from apps.electron.filters import ElectronFilter


# Create your views here.
# 元器件分类
from apps.scheme.models import SchemeElectron


class ElectronCategoryViewSet(viewsets.ModelViewSet):
    """
        retrieve:
           元器件分类详情
        list:
           元器件分类列表（无子类）
        categories_list:
           元器件分类列表（有子类）
        categories_list_level:
           元器件分类列表（最多二级子类）
        kwargs:
           分类元器件参数列表
        create:
           元器件分类新增
        delete:
           元器件分类删除
        update:
           元器件分类更新
    """
    queryset = ElectronCategory.objects.all()
    serializer_class = ElectronCategoryListSerializer

    @action(['get'], detail=True)
    def kwargs(self, request, *args, **kwargs):
        try:
            # electron_category_id = request.query_params['id']
            electon_category = self.get_object()
            kwargs = ElectronKwargs.objects.filter(category=electon_category)
            page = self.paginate_queryset(kwargs)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except ElectronCategory.DoesNotExist:
            return Response({"count": 0, "results": []}, status=status.HTTP_200_OK)

    @action(['get'], detail=False)
    def categories_list(self, request):
        electron_categories = ElectronCategory.objects.filter(parent=None)
        serializer = ElectronCategoryListSerializer(electron_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['get'], detail=False)
    def categories_list_level(self, request):
        electron_categories = ElectronCategory.objects.filter(parent=None)
        serializer = ElectronCategorySerializer2(electron_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == 'categories_list':
            return ElectronBackListSerializer
        return ElectronCategorySerializer


# 元器件详情
class ElectronViewSet(viewsets.ModelViewSet, viewsets.GenericViewSet):
    """
        list:
           产品列表
        retrieve:
           产品详情
        delete:
           产品删除
        hot_electron:
           热门元器件
        apply:
           应用支持（提交）
        applys:
           应用支持（获取）
        videos:
           产品对应的视图
        schemes:
           产品参考设计
        plist:
           pintopin产品列表
        psearch:
           PinToPin搜索匹配
        slist:
            可替换产品列表
        ssearch:
            可替换产品搜索匹配
    """

    serializer_class = ElectronSerializer
    pagination_class = ElectronPagination
    filter_backends = [DjangoFilterBackend]
    filter_class = ElectronFilter

    def get_queryset(self):
        queryset = Electron.objects.filter(isDelete=False).order_by('-create_at')
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ElectronBackListSerializer
        elif self.action == 'retrieve':
            return ElectronDetailSerializer
        elif self.action == 'apply' or self.action == 'applys':
            return ElectronApplySerializer
        elif self.action == 'supplier':
            return ElectronSupplierListSerializer
        elif self.action == 'videos':
            return ElectronVideoSerializer
        elif self.action == 'schemes':
            return ElectronSchemeSerializer
        elif self.action in ['psearch', 'ssearch']:
            return ElectronModelSerializer
        elif self.action == 'plist':
            return ElectronPlistSerializer
        elif self.action == 'slist':
            return ElectronSlistSerializer
        elif self.action == 'create':
            return ElectronRetrieveCreateSerializer
        else:
            return ElectronSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.isDelete = True
        instance.save()
        self.perform_destroy(instance)
        return Response({"success": "删除产品成功!"}, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"success": "添加元器件成功!"}, status=status.HTTP_201_CREATED)

    @action(['get'], detail=False)
    def hot_electron(self, request):
        """热搜产品配置"""
        try:
            model_name = request.query_params['model_name']
            electron = Electron.objects.get(model_name=model_name)
            electron.is_hot = (not electron.is_hot)
            electron.save()
            return Response({'message': 'ok'}, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({'message': 'error'}, status=status.HTTP_400_BAD_REQUEST)

    # detail=True 需要指定  *args, **kwargs 参数
    @action(['post'], detail=True)
    def apply(self, request, *args, **kwargs):
        """应用支持（提交）"""
        try:
            electron = self.get_object()
            factory_link = request.data['factory_link']
            electron.factory_link = factory_link
            electron.save()
            return Response({"message": "ok"}, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({"message": '提交失败'}, status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=True)
    def applys(self, request, *args, **kwargs):
        """应用支持（获取）"""
        try:
            electron = self.get_object()
            serializer = self.get_serializer(electron)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({"message": '没查找到应用支持'}, status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=True)
    def supplier(self, request, *args, **kwargs):
        """获取元器件对应的供应商列表"""
        try:
            electron = self.get_object()
            queryset = ElectronSupplier.objects.filter(electron=electron)
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Electron.DoesNotExist:
            message = {"count": 0, "results": []}
            return Response(message, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def videos(self, request, *args, **kwargs):
        """元器件对应的视频"""
        try:
            electron = self.get_object()
            queryset = ElectronVideo.objects.filter(electron=electron)
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Electron.DoesNotExist:
            message = {"count": 0, "results": []}
            return Response(message, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def schemes(self, request, *args, **kwargs):
        """元器件方案列表（参考设计）"""
        try:
            electron = self.get_object()
            scheme_electrons = Scheme.objects.filter(electrons__model_name__model_name=electron, is_reference=True)
            queryset = [scheme_electron for scheme_electron in scheme_electrons]
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except SchemeElectron.DoesNotExist:
            message = {"count": 0, "results": []}
            return Response(message, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def plist(self, request, *args, **kwargs):
        """pin_to_pin产品列表"""
        try:
            electron = self.get_object()
            queryset = PinToPin.objects.filter(electron=electron)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def psearch(self, request, *args, **kwargs):
        """pin_to_pin搜索匹配"""
        try:
            model_name = request.query_params['model_name']
            electron = Electron.objects.get(id=int(kwargs['pk']))
            pintopins = [p.pin_to_pin for p in PinToPin.objects.filter(electron=electron)]
            electrons = list(Electron.objects.filter(model_name__istartswith=model_name))
            if len(pintopins) == 0:
                serializer = self.get_serializer(electrons, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            electrons = list(set(electrons).difference(set(pintopins)))[:10]
            serializer = self.get_serializer(electrons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({}, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def slist(self, request, *args, **kwargs):
        """可替换产品列表"""
        try:
            electron = self.get_object()
            queryset = SimilarElectron.objects.filter(electron=electron)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def alist(self, request, *args, **kwargs):
        try:
            electron = self.get_object()
            queryset = SimilarElectron.objects.filter(electron=electron)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def ssearch(self, request, *args, **kwargs):
        """可替换产品搜索匹配"""
        try:
            model_name = request.query_params['model_name']
            electron = Electron.objects.get(id=int(kwargs['pk']))
            similars = [p.similar for p in SimilarElectron.objects.filter(electron=electron)]
            electrons = Electron.objects.filter(model_name__istartswith=model_name)
            if len(similars) == 0:
                serializer = self.get_serializer(electrons, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            electrons = list(set(electrons).difference(set(similars)))[:10]
            serializer = self.get_serializer(electrons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({}, status=status.HTTP_200_OK)


# 元器件分类
class ElectronsCategoryListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ElectronCategoryAllSerializer3
    queryset = Electron.objects.all()

    def list(self, request, *args, **kwargs):
        electron_categories = ElectronCategory.objects.filter(parent=None)
        serializer = ElectronCategoryAllSerializer(electron_categories, many=True)

        for i, j in enumerate(serializer.data):
            if not serializer.data[i]['children']:
                serializer.data[i]['children'] = None

            else:
                for a, b in enumerate(serializer.data[i]['children']):

                    if not serializer.data[i]['children'][a]['children']:
                        serializer.data[i]['children'][a]['children'] = None

        return Response(serializer.data, status=status.HTTP_200_OK)


# 元器件更新
class ElectronRetrieveUpdate(UpdateAPIView):
    """
    元器件更新
    """
    queryset = Electron.objects.all()
    serializer_class = ElectronRetrieveUpdateSerializer

    def update(self, request, *args, **kwargs):
        validated_data = request.data
        id = validated_data['id']
        model_name = validated_data['model_name']
        images = validated_data['images']
        data_sheet_name = validated_data['data_sheet_name']
        data_sheet = validated_data['data_sheet']
        desc_specific = validated_data['desc_specific']
        electron_kwargs = validated_data['electron_kwargs']
        is_supply = validated_data['is_supply']
        origin = validated_data['origin']
        factory = validated_data['factory']
        market_date_at = validated_data['market_date_at']
        platform_price = validated_data['platform_price']
        platform_stock = validated_data['platform_stock']

        with transaction.atomic():
            save_id = transaction.savepoint()
            electron = Electron.objects.get(id=id)
            electron1 = Electron.objects.filter(id=id)
            electron1.update(
                model_name=model_name,
                factory=factory,
                images=images,
                data_sheet=data_sheet,
                data_sheet_name=data_sheet_name,
                desc_specific=desc_specific,
                origin=origin,
                is_supply=is_supply,
                market_date_at=market_date_at,
                platform_price=platform_price,
                platform_stock=platform_stock,
            )
            if not electron:
                transaction.savepoint_rollback(save_id)
                return Response({"message": "产品更新失败"}, status=status.HTTP_400_BAD_REQUEST)

            if electron_kwargs:
                electron_list = []
                for kwargs in electron_kwargs:
                    if kwargs['id']:
                        electron_list.append(kwargs['id'])
                        electron_kwargs_value = ElectronKwargsValueFront.objects.filter(id=kwargs['id']).update(
                            electron=kwargs['electron'],
                            kwargs_name=kwargs['kwargs_name'],
                            kwargs_value=kwargs['kwargs_value'],
                        )

                    if kwargs['id'] == '':
                        electron_kwargs_value = ElectronKwargsValueFront.objects.create(
                            electron_id=kwargs['electron'],
                            kwargs_id=kwargs['kwargs'],
                            kwargs_name=kwargs['kwargs_name'],
                            kwargs_value=kwargs['kwargs_value'],
                        )
                        electron_list.append(electron_kwargs_value.id)
                        if not electron_kwargs_value:
                            transaction.savepoint_rollback(save_id)
                            return Response({"message": "更新产品参数失败"}, status=status.HTTP_400_BAD_REQUEST)
            transaction.savepoint_commit(save_id)
        return Response({"message": "产品更新成功"}, status=status.HTTP_200_OK)


# 供应商添加
class SupplierRetrieveCreate(CreateAPIView):
    """
    供应商添加
    """
    queryset = Supplier.objects.all()
    serializer_class = ElectronCreateSupplierSerlializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "添加供应商成功!"}, status=status.HTTP_201_CREATED)


# 视频添加
class VideoRetrieveCreate(CreateAPIView):
    """
    视频添加
    """
    queryset = ElectronVideo.objects.all()
    serializer_class = ElectronCreateVideoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "添加成品成功!"}, status=status.HTTP_201_CREATED)


# 分类参数列表返回
class ElectronKwargsListViewSet(ListModelMixin, viewsets.GenericViewSet):
    queryset = ElectronKwargs.objects.all()
    serializer_class = ElectronsKwargsSerializer

    def list(self, request, *args, **kwargs):
        try:
            electron = request.query_params['category']
            queryset = ElectronKwargs.objects.filter(electron_id=int(electron))
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Electron.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)


# 添加供应商
class ElectronRetrieveCreateSupplier(viewsets.ModelViewSet):
    """
    添加供应商
    """
    queryset = ElectronSupplier.objects.all()
    serializer_class = ElectronCreateSupplierSerlializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ElectronSupplierListSerializer
        elif self.action == 'create':
           return ElectronCreateSupplierSerlializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "添加供应商成功!"}, status=status.HTTP_201_CREATED)


# 添加视频
class ElectronRetrieveCreateVideo(viewsets.ModelViewSet):
    """
    添加视频
    """
    queryset = ElectronVideo.objects.all()
    serializer_class = ElectronCreateSupplierSerlializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ElectronVideoSerializer
        elif self.action == 'create':
           return ElectronCreateVideoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "添加视频成功!"}, status=status.HTTP_201_CREATED)


# 文件上传接口
class FileStorageViewSet(viewsets.ModelViewSet):
    """文件上传接口"""
    queryset = ElectronFile.objects.all()
    serializer_class = FileSerializer


# 可替代产品
class SimilarElectronViewSet(generics.CreateAPIView, generics.DestroyAPIView, viewsets.GenericViewSet):
    """
        create:
            可替换产品新增
        delete:
            可替换产品删除
    """
    queryset = SimilarElectron.objects.all()
    serializer_class = SimilarElectronSerializer

    @action(['get'], detail=True)
    def similar_list(self, request):
        """获取元器件对应的可替换器件列表"""
        try:
            electron_id = request.query_params.get('id', None)
            electron = Electron.objects.get(pk=electron_id)
            similar_electrons = SimilarElectron.objects.filter(electron=electron)
            electrons = [similar.electron for similar in similar_electrons]
            serializer = ElectronSerializer(data=electrons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({"message": '暂无元器件供应商'}, status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=True)
    def similar_add_list(self, request):
        """查询可添加的可替换器件列表"""
        try:
            electron_id = request.query_params.get('id', None)
            electron = Electron.objects.get(pk=electron_id)
            similars = [similar.electron for similar in SimilarElectron.objects.filter(electron=electron)]
            electrons = Electron.objects.all()
            electrons = list(set(electrons).difference(set(similars)))
            serializer = ElectronModelSerializer(electrons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            pass

    @action(['get'], detail=True)
    def del_similar_electron(self, request):
        """可替代元器件删除"""
        try:
            similar_id = request.query_params['id']
            similar_electron = SimilarElectron.objects.get(id=similar_id)
            similar_electron.delete()
            return Response({'message': 'ok'}, status=status.HTTP_200_OK)
        except SimilarElectron.DoesNotExist:
            return Response({'message': 'error'}, status=status.HTTP_400_BAD_REQUEST)


# 供应商信息
class SupplierListViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all()
    pagination_class = SupplierPagination


class EletronSupplierViewSet(viewsets.ModelViewSet):
    serializer_class = ElectronSupplierSerializer
    queryset = ElectronSupplier.objects.all()
    pagination_class = SupplierPagination


# 元器件电路图
class ElectronCircuitDiagramViewSet(generics.ListCreateAPIView, viewsets.GenericViewSet):
    queryset = ElectronCircuitDiagram.objects.all()
    serializer_class = ElectronCircuitDiagramSerializer

    def electron_list(self, request, *args, **kwargs):
        """元器件对应的原理图"""
        electron_id = request.query_parmas.get('electron_id', None)
        if electron_id:
            electron = Electron.objects.get(id=electron_id)
            electron_diagrams = ElectronCircuitDiagram.objects.filter(electron=electron)
            serializer = ElectronCircuitDiagramSerializer(electron_diagrams, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'error'}, status=status.HTTP_400_BAD_REQUEST)


# 元器件类型参数
class ElectronKwargsViewSet(viewsets.ModelViewSet, viewsets.GenericViewSet):
    """
        retrieve:
           元器件参数详情
        list:
           元器件参数列表
        electons_kwargs_list:
           元器件类型参数列表（同类型）
        create:
           元器件参数新增
        delete:
           元器件参数删除
        update:
           元器件更新更新
    """

    queryset = ElectronKwargs.objects.all()
    serializer_class = ElectronKwargsSerializer
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == 'list':
            return ElectronKwargsSerializer
        elif self.action == 'create':
            return ElectronKwargsValueSerializer
        else:
            return ElectronKwargsSerializer

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                self.perform_update(serializer)
                values = request.data['values']
                ElectronKwargsValue.objects.filter(kwargs=instance).delete()
                for value in values.split(','):
                    kv = ElectronKwargsValue(kwargs=instance, value=value)
                    kv.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=False)
    def electons_kwargs_list(self, request):
        try:
            electron_category_id = request.query_params['id']
            electron_category = ElectronCategory.objects.get(id=electron_category_id)
            kwargs = ElectronKwargs.objects.filter(electron=electron_category)

            page = self.paginate_queryset(kwargs)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        except ElectronCategory.DoesNotExist:
            return Response({"count": 0, "results": []}, status=status.HTTP_200_OK)


# 元器件视频
class ElectronVideoViewSet(viewsets.GenericViewSet):
    """
        primary:
        设为主视频
    """
    queryset = ElectronVideo.objects.all()
    serializer_class = ElectronVideoSerializer

    @action(['get'], detail=True)
    def primary(self, request, *args, **kwargs):
        electron_video = self.get_object()
        try:
            primary_electron = ElectronVideo.objects.get(electron=electron_video.electron, is_primary=True)
            primary_electron.is_primary = False
            primary_electron.save()
        except Exception as e:
            print(e)
        electron_video.is_primary = True
        electron_video.save()
        return Response({'message': 'ok'}, status=status.HTTP_200_OK)


# PinToPo元器件消费者
class ElectronConsumerViewSet(viewsets.ModelViewSet):
    queryset = ElectronConsumer.objects.all()
    serializer_class = ElectronConsumerSerializer


# PinToPin元器件
class PinToPinViewSet(generics.DestroyAPIView, generics.CreateAPIView, viewsets.GenericViewSet):
    """
    destory:
    PintoPin产品删除
    create:
    PintoPin产品新增
    """
    queryset = PinToPin.objects.all()
    serializer_class = PinToPinCreateSerializer





