from rest_framework import (viewsets, status, generics, filters, mixins)
from rest_framework.response import Response
from apps.scheme.pagination import *
# from .serializers import ElectronCategorySerializer, ElectronSerializer
from apps.scheme.serializer.serializers_back import *
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, UpdateAPIView
from datetime import datetime
from apps.scheme.filters import SchemeFilter
# ---------管理后台界面逻辑------------
# 方案类型
class SchemeCategoryViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
        retrieve:
           方案分类详情
        list:
           方案分类列表 (无子分类)
        categories_list:
           方案分类列表（有子分类）
        create:
           方案分类新增
        delete:
           方案分类删除
        update:
           方案分类更新
    """
    queryset = SchemeCategory.objects.all()
    serializer_class = SchemeCategorySerializer3

    @action(['get'], detail=False)
    def categories_list(self, request):
        scheme_categories = SchemeCategory.objects.filter(parent=None)
        serializer = SchemeCategoryListSerializer(scheme_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 方案
class SchemeViewSet(mixins.CreateModelMixin,viewsets.GenericViewSet, generics.DestroyAPIView, generics.RetrieveUpdateAPIView, generics.ListAPIView):
    """
        delete:
            方案删除
        update:
            方案更新
        retrieve:
            方案详情
        list:
            方案列表
        selectron:
            详情元器件搜索
        slist:
            可替代方案列表
        similars:
            可替换方案的添加列表： title：标题参数， source_web: 网站来源参数
    """
    queryset = Scheme.objects.all()
    serializer_class = SchemeDetailSerializer
    filter_backends = [filters.SearchFilter]
    filter_class = SchemeFilter
    search_fields = ['title', 'source_web']
    pagination_class = SchemePagination

    def get_serializer_class(self):
        if self.action == 'list':
            return SchemeListSerializer
        elif self.action =='retrieve':
            return SchemeDetailRetrieveSerializer
        elif self.action == 'create':
            return SchemeUpdateSerializer
        elif self.action == 'slist':
            return SimilarSchemeSerializer
        elif self.action == 'similars':
            return SimilarSchemeListSerializer
        else:
            return SchemeDetailSerializer

    @action(['get'], detail=True)
    def selectron(self, request, *args, **kwargs):
        try:
            scheme = self.get_object()
            model_name = request.query_params['model_name']
            m_models = [e.model_name for e in SchemeElectron.objects.filter(scheme=scheme, model_name__istartswith=model_name)]
            models = [e.model_name for e in Electron.objects.filter(model_name__istartswith=model_name)]
            models_result = list(set(models).difference(set(m_models)))[:10]
            return Response({'models': models_result}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'models': '未匹配到模型数据'}, status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=True)
    def slist(self, request, *args, **kwargs):
        """相似方案列表"""
        try:
            scheme = self.get_object()
            queryset = SimilarScheme.objects.filter(scheme=scheme)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def similars(self, request, *args, **kwargs):
        """可替换方案的添加列表"""
        scheme = self.get_object()
        similars = [s.similar for s in SimilarScheme.objects.filter(scheme=scheme)]
        schemes = Scheme.objects.all()
        title = request.query_params.get('title', None)
        source_web = request.query_params.get('source_web', None)
        if title:
            schemes = schemes.filter(model_name__istartswith=title)
        if source_web:
            schemes = schemes.filter(source_web=source_web)
        queryset = list(set(schemes).difference(set(similars)))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def all_search(self, request, *args, **kwargs):
        try:
            model_name = request.query_params['model_name']
            electrons = list(Electron.objects.filter(model_name__istartswith=model_name))
            serializer = self.get_serializer(electrons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({}, status=status.HTTP_200_OK)

class SchemeRetrieveUpdate(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Scheme.objects.all()
    serializer_class = SchemeRetrieveUpdateSerializer

    def update(self, request, *args, **kwargs):
        validated_data = request.data
        id = validated_data['id']
        title = validated_data['title']
        price = validated_data['price']
        category = validated_data['category'][len(validated_data['category']) - 1]
        images = validated_data['images']
        videos = validated_data['videos']
        designs = validated_data['designs']
        electrons = validated_data['electrons']
        desc_specific = validated_data['desc_specific']
        source_code = validated_data['source_code']
        code_name = validated_data['code_name']
        contact_name = validated_data['contact_name']
        contact_tel = validated_data['contact_tel']
        enterprise = validated_data['enterprise']
        contact_qq = validated_data['contact_qq']
        contact_email = validated_data['contact_email']
        is_reference =validated_data['is_reference']

        with transaction.atomic():
            save_id = transaction.savepoint()
            scheme = Scheme.objects.get(id=id)
            scheme1 = Scheme.objects.filter(id=id)
            scheme1.update(
                title=title,
                price=price,
                category=category,
                images=images,
                desc_specific=desc_specific,
                source_code=source_code,
                code_name=code_name,
                contact_name=contact_name,
                contact_tel=contact_tel,
                enterprise=enterprise,
                contact_qq=contact_qq,
                contact_email=contact_email,
                is_reference=is_reference
            )
            if not scheme:
                transaction.savepoint_rollback(save_id)
                return Response({"message": "方案更新失败"}, status=status.HTTP_400_BAD_REQUEST)


            if videos:
                video_list = []
                for video in videos:
                    if video['id']:
                        video_list.append(video['id'])
                    if video['id'] == '':
                        scheme_video = SchemeVideo.objects.create(
                            scheme=scheme,
                            url=video['url'],
                            is_primary=video['is_primary'],
                        )
                        video_list.append(scheme_video.id)
                        if not scheme_video:
                            transaction.savepoint_rollback(save_id)
                            return Response({"message": "方案更新失败"}, status=status.HTTP_400_BAD_REQUEST)
            	
                ids = SchemeVideo.objects.filter(scheme=scheme)
                for i in ids:
                    if i.id not in video_list:
                        SchemeVideo.objects.get(id=i.id).delete()
            else:
                SchemeVideo.objects.filter(scheme=scheme).delete()

            if designs:
                id_list = []
                for design in designs:
                    if design['id']:
                        id_list.append(design['id'])
                    if design['id'] == '':
                        scheme_design = SchemeSystemDesign.objects.create(
                            scheme=scheme,
                            name=design['name'],
                            image=design['image'],
                        )
                        id_list.append(scheme_design.id)

                        if not scheme_design:
                            transaction.savepoint_rollback(save_id)
                            return Response({"message": "方案更新失败"}, status=status.HTTP_400_BAD_REQUEST)
    
                ids = SchemeSystemDesign.objects.filter(scheme=scheme)
                for i in ids:
                    if i.id not in id_list:
                        SchemeSystemDesign.objects.get(id=i.id).delete()
            else:
                SchemeSystemDesign.objects.filter(scheme=scheme).delete()
            if electrons:
                for electron in electrons:
                    model_name = Electron.objects.get(model_name=electron['model_name'])
                    if electron['id']:
                        scheme_ele = SchemeElectron.objects.filter(id=electron['id']).update(
                            model_name=model_name.id,
                            model_des=electron['model_des'],
                        )
                    else:
                        scheme_ele = SchemeElectron.objects.create(
                            scheme=scheme,
                            model_name=model_name,
                            model_des=electron['model_des'],
                            is_key=electron['is_key'],
                            is_record=True,
                            create_at=datetime.now()
                        )

                    if not scheme_ele:
                        transaction.savepoint_rollback(save_id)
                        return Response({"message": "方案更新失败"}, status=status.HTTP_400_BAD_REQUEST)
            transaction.savepoint_commit(save_id)
        return Response({"message": "方案更新成功"}, status=status.HTTP_200_OK)

# 方案分类
class BackSchemeCategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SchemeCategorySerializer3
    queryset = SchemeCategory.objects.all()

    def list(self, request, *args, **kwargs):
        scheme_categories = SchemeCategory.objects.filter(parent=None)
        serializer = SchemeCategoryListSerializer(scheme_categories, many=True)
        for i, j in enumerate(serializer.data):
            if not serializer.data[i]['children']:
                serializer.data[i]['children'] = None
            else:
                for a, b in enumerate(serializer.data[i]['children']):
                    if not serializer.data[i]['children'][a]['children']:
                        serializer.data[i]['children'][a]['children'] = None

        return Response(serializer.data, status=status.HTTP_200_OK)

# 方案bom元器件
class SchemeBomElectronViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Electron.objects.all()
    serializer_class = SchemeElectronSearchSerializer

    def list(self, request, *args, **kwargs):
        model_name = request.query_params['model_name']
        queryset = Electron.objects.filter(model_name__istartswith=model_name)
        serializer =  SchemeElectronSearchSerializer(queryset, many=True)

        return Response(serializer.data, status.HTTP_200_OK)

class SchemeBomElectronDeleteViewset(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = SchemeElectron.objects.all()
    serializer_class = SchemeElectronSerializer


# # 方案DataSheet文件上传
# class ElectronDataSheetViewSet(generics.UpdateAPIView, generics.DestroyAPIView, viewsets.GenericViewSet):
#     """
#         delete:
#            元器件DataSheet文件删除
#         update:
#            元器件DataSheet文件更新
#     """
#     queryset = Scheme.objects.all()
#     serializer_class = SchemeDataSheetSerializer
#
#     def perform_destroy(self, instance):
#         instance.source_code = ""
#         instance.save()
#
#
# # 方案图片
# class SchemeImageViewSet(generics.UpdateAPIView, generics.DestroyAPIView, viewsets.GenericViewSet):
#     """
#         delete:
#            方案Image文件删除
#         update:
#            方案Image文件更新
#     """
#     queryset = Scheme.objects.all()
#     serializer_class = SchemeUploadImageSerializer
#
#     def perform_destroy(self, instance):
#         instance.images = ""
#         instance.save()


# # 方案系统图
# class SchemeSystemDesignViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
#     """
#         create:
#             方案系统图新增
#         update:
#             方案系统图修改
#         destroy:
#             方案系统图删除
#     """
#     queryset = SchemeSystemDesign.objects.all()
#     serializer_class = SchemeSystemDesignSerializer


# 方案视频
# class SchemeVideoViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
#     """
#             create:
#                 方案视频新增
#             update:
#                 方案视频修改
#             destroy:
#                 方案视频删除
#     """
#
#     queryset = SchemeVideo.objects.all()
#     serializer_class = SchemeVideoSerializer


# 方案Bom清单
class SchemeElectronViewSet(viewsets.ModelViewSet):
    """方案Bom清单"""
    queryset = SchemeElectron.objects.all()
    serializer_class = SchemeElectronSerializer
    pagination_class = SchemeElectronPagination

    @action(['get'], detail=False)
    def scheme_list(self, request, *args, **kwargs):
        """元器件方案列表（参考设计）"""
        try:
            model_name = request.query_params['model_name']
            scheme_electrons = SchemeElectron.objects.filter(model_name=model_name)
            schemes = [scheme_electron.scheme for scheme_electron in scheme_electrons]
            reference_schemes = []
            for scheme in schemes:
                if scheme.is_reference:
                    reference_schemes.append(scheme)
            serializer = SchemeSerializer(reference_schemes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SchemeElectron.DoesNotExist:
            return Response({"message": "error"}, status=status.HTTP_400_BAD_REQUEST)

    @action(['get'], detail=False)
    def electron_list(self, request, *args, **kwargs):
        """方案元器件列表"""
        try:
            scheme_id = request.query_params['scheme_id']
            scheme = Scheme.objects.get(id=scheme_id)
            scheme_electrons = SchemeElectron.objects.filter(scheme=scheme)
            schemes = [scheme_electron.scheme for scheme_electron in scheme_electrons]
            serializer = SchemeSerializer(schemes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SchemeElectron.DoesNotExist:
            return Response({"message": "error"}, status=status.HTTP_400_BAD_REQUEST)


# 可替代方案(数据库中已经关联匹配方案)
class SimilarSchemeViewSet(generics.DestroyAPIView, generics.CreateAPIView, viewsets.GenericViewSet):
    queryset = SimilarScheme.objects.all()
    serializer_class = SimilarSchemeSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return SimilarSchemeSerializer
        else:
            return SimilarSchemeCreateSerializer


# 方案消费者
class SchemeConsumerViewSet(viewsets.ModelViewSet):
    queryset = SchemeConsumer.objects.all()
    serializer_class = SchemeConsumerSerializer

    def list(self, request, *args, **kwargs):
        """元器件方案列表"""
        try:
            electron_id = request.query_params['electron_id']
            electron = Electron.objects.get(id=electron_id)
            scheme_electrons = SchemeElectron.objects.filter(electron=electron)
            schemes = [scheme_electron.scheme for scheme_electron in scheme_electrons]
            serializer = SchemeSerializer(schemes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SchemeElectron.DoesNotExist:
            return Response({"message": "error"}, status=status.HTTP_400_BAD_REQUEST)

