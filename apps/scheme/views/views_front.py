from django.http import HttpResponse
from rest_framework import (viewsets, status, generics, filters, mixins)
from rest_framework.generics import CreateAPIView, UpdateAPIView,ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.scheme.serializer.serializers_front import *
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.scheme.pagination import SchemePagination
from django.http import JsonResponse
import json
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from django.db.models import Q,F
from datetime import datetime


class SchemeDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """

    slist:相似方案列表
    diagram’：系统框图
    share ： 方案分享

    """
    queryset = Scheme.objects.all()
    serializer_class = SchemeSerializer
    pagination_class = SchemePagination




    def get_serializer_class(self):
        if self.action == 'diagram':
            return FrontSchemeDesignSerializer
        elif self.action == 'slist':
            return ReferenceSchemeSerializer
        # elif self.action == 'slist':
        #     return SimilarSchemeSerializer
        # elif self.action == 'master':
        #     return SchemeMasterSerializer
        # elif self.action =='similarBom':
        #     return SimilarBomSerializers
        elif self.action == 'share':
            return SchemeDownSerializer
        else:
            return SchemeDetailPageSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views +=1
        instance.save()
        serializer = self.get_serializer(instance)
        if self.request.user.username:
            username = self.request.user.username
            conn = get_redis_connection("browsing_history")

            scheme = Scheme.objects.get(id=int(kwargs['pk']))
            scheme_category_id = scheme.category_id
            category_id = conn.get("%s_recommend_scheme_category_id" % username)
            if not category_id or int(category_id) != scheme_category_id:
                conn.setex("%s_recommend_scheme_category_id" % username, 7 * 24 * 60 * 60, scheme_category_id)

        return Response(serializer.data)

    @action(['get'], detail=True)
    def slist(self, request, *args, **kwargs):
        """相似方案列表"""
        try:
            scheme = self.kwargs['pk']
            category = Scheme.objects.get(id=int(scheme)).category

            queryset = Scheme.objects.filter(Q(category=category)&~Q(id=scheme))
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)
        #
        # try:
        #     scheme = self.kwargs['pk']
        #     queryset = SimilarScheme.objects.filter(scheme=int(scheme))
        #
        #     page = self.paginate_queryset(queryset)
        #     if page is not None:
        #         serializer = self.get_serializer(page, many=True)
        #         return self.get_paginated_response(serializer.data)
        #     serializer = self.get_serializer(queryset, many=True)
        #     return Response(serializer.data, status=status.HTTP_200_OK)
        # except Electron.DoesNotExist:
        #     return Response({}, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def diagram(self, request, *args, **kwargs):
        """系统框图"""
        try:
            scheme = self.kwargs['pk']
            queryset = SchemeSystemDesign.objects.filter(scheme=int(scheme))
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Electron.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

    @action(['get'], detail=True)
    def share(self, request, *args, **kwargs):
        """方案分享下载"""
        scheme = self.kwargs['pk']

        # user = request.user
        instance = Scheme.objects.get(id=scheme)
        instance.download_count +=1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #
    # @action(['get'], detail=True)
    # def master(self,request, *args, **kwargs):
    #     """方案大师"""
    #     try:
    #         scheme = self.kwargs['pk']
    #         queryset = Scheme.objects.filter(scheme=int(scheme))
    #         serializer = self.get_serializer(queryset, many=True)
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     except Electron.DoesNotExist:
    #         return Response({}, status=status.HTTP_200_OK)


# 个人方案创建
class NewSchemeViewSet(CreateAPIView, UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Scheme.objects.all()
    serializer_class = NewSchemeSerializer

    def update(self, request, *args, **kwargs):
        validated_data= request.data
        id = validated_data['id']
        title = validated_data['title']
        price = validated_data['price']
        category = validated_data['category'][len(validated_data['category'])-1]
        images = validated_data['images']
        videos = validated_data['videos']
        designs = validated_data['designs']
        electrons = validated_data['electrons']
        desc_specific = validated_data['desc_specific']
        source_code = validated_data['source_code']
        code_name= validated_data['code_name']
        contact_name = validated_data['contact_name']
        contact_tel = validated_data['contact_tel']
        enterprise = validated_data['enterprise']
        contact_qq = validated_data['contact_qq']
        contact_email = validated_data['contact_email']

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
                code_name = code_name,
                contact_name=contact_name,
                contact_tel=contact_tel,
                enterprise=enterprise,
                contact_qq=contact_qq,
                contact_email=contact_email,
            )
            if not scheme:
                transaction.savepoint_rollback(save_id)
                return Response({"message": "方案更新失败"},status=status.HTTP_400_BAD_REQUEST)
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
                    if design['id'] =='':
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
                        scheme_ele=SchemeElectron.objects.create(
                        scheme=scheme,
                        model_name=model_name,
                        model_des=electron['model_des'],
                        is_key=electron['is_key'],
                        is_record=True,
                        create_at=datetime.now()
                    )

                    if not scheme_ele:
                        transaction.savepoint_rollback(save_id)
                        return Response({"message": "方案更新失败"},status=status.HTTP_400_BAD_REQUEST)
            transaction.savepoint_commit(save_id)
        return Response({"message": "方案更新成功"},status=status.HTTP_200_OK)


# 个人方案详情
class NewSchemeDetailViewSet(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Scheme.objects.all()
    serializer_class = NewSchemeDetailSerializer
    pagination_class = SchemePagination

    def get_queryset(self):
        queryset= Scheme.objects.filter(scheme_user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return NewSchemeListSerializer

        return NewSchemeDetailSerializer

# 方案分类
class NewSchemeCategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NewSchemeCategorySerializer3
    queryset = SchemeCategory.objects.all()

    def list(self, request, *args, **kwargs):
        scheme_categories = SchemeCategory.objects.filter(parent=None)
        serializer = NewSchemeCategoryListSerializer(scheme_categories, many=True)
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
    serializer_class = SchemeElectronSerializer

    def list(self, request, *args, **kwargs):
        model_name = request.query_params['model_name']
        queryset = Electron.objects.filter(model_name__istartswith=model_name)
        serializer = SchemeElectronSerializer(queryset, many=True)

        return Response(serializer.data[:10], status.HTTP_200_OK)


class SchemeElectronDeleteViewset(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = SchemeElectron.objects.all()
    serializer_class = NewSchemeElectronSerializer



class SchemeSimilarSearch(generics.GenericAPIView):
    queryset = SimilarScheme.objects.all()
    serializer_class = SearchSimilarSchemeSerializer
    pagination_class = SchemePagination

    def get(self,request):
        data = request.query_params
        param_dict1 = {}
        id = data['id']
        try:
            scheme = Scheme.objects.get(id=id)
        except:
            return Response({'message': '相关方案不存在', 'status': 301})
        param_dict1['scheme'] = id
        category = data['category']
        is_reference = data['is_reference']
        if category:
            param_dict1['similar__category'] = category
        if is_reference:
            param_dict1['similar__is_reference'] = is_reference
        similar = SimilarScheme.objects.filter(**param_dict1)
        page = self.paginate_queryset(similar)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializers = SearchSimilarSchemeSerializer(similar,many=True)

        serializers.data.append({'count':0})
        return Response(serializers.data)


class SchemeProductSearch(generics.GenericAPIView):
    queryset = Product.objects.all()
    serializer_class = SchemeProductSerializer
    pagination_class = SchemePagination

    def get(self,request,*args, **kwargs):
        data = request.query_params
        param_dict2 = {}
        id = data['id']
        try:
            scheme = Scheme.objects.get(id=id)
        except:
            return Response({'message': '相关产品不存在', 'status': 301})
        category = data['category_id']
        origin = data['origin']
        market_date_at = data['market_date_at']
        if category:
            param_dict2['category'] = category
        if origin:
            param_dict2['origin'] = origin
        if market_date_at:
            param_dict2['market_date_at__gte'] = datetime.strptime(market_date_at,'%Y')
            param_dict2['market_date_at__lt'] = datetime.strptime(str(int(market_date_at)+1),'%Y')
        product= Scheme.objects.get(id=id).products.filter(**param_dict2)
        page = self.paginate_queryset(product)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializers= SchemeProductSerializer(product,many=True)
        return Response(serializers.data)


class SchemeElectronSearch(generics.GenericAPIView):
    queryset = SchemeElectron.objects.all()
    serializer_class = SchemeIncludeElectronSerializer
    pagination_class = SchemePagination

    def get(self,request):
        data = request.query_params
        param_dict3 = {}
        id = data['id']
        try:
            scheme = Scheme.objects.get(id=id)
        except:
            return Response({'message': '相关方案不存在', 'status': 301})
        param_dict3['scheme'] =id
        origin = data['origin']
        platform_price_min = data['platform_price_min']
        platform_price_max = data['platform_price_max']
        market_date_at = data['market_date_at']
        if origin:
            param_dict3['model_name__origin'] = origin
        if platform_price_max:
            param_dict3['model_name__platform_price__lte'] = platform_price_max
        if platform_price_min:
            param_dict3['model_name__platform_price__gte'] = platform_price_min
        if market_date_at:
            param_dict3['model_name__market_date_at__gte'] = datetime.strptime(market_date_at,'%Y')
            param_dict3['model_name__market_date_at__lt'] = datetime.strptime(str(int(market_date_at)+1),'%Y')

        queryset = SchemeElectron.objects.filter(**param_dict3)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializers = SchemeIncludeElectronSerializer(queryset,many=True)
        return Response(serializers.data)


class IndexSchemeSearch(APIView):

    def get(self,request):

        title = request.query_params['title']
        scheme = Scheme.objects.filter(title__icontains=title)
        serializers =  IndexSchemeSearchSerializer(scheme,many=True)

        return Response(serializers.data)