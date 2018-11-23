from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import (generics, status, authentication, permissions, filters, viewsets, routers, mixins)
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
import json
from apps.electron.models import Electron
from apps.electron.serializer.serializers_back import ElectronSerializer
from .serializers import *
from apps.config.models import FreightCarrier, MagicContent, MagicContentCategory
from apps.product.pagination import Pagination



# 运费配置
class FreightViewSet(viewsets.ModelViewSet):
    serializer_class = FreightSerializer
    queryset = FreightCarrier.objects.all()

    def list (self, request, *args, **kwargs):
        queryset = self.queryset
        serializer = self.get_serializer(queryset, many=True)
        if not serializer.data:
            return Response({"message": "无数据"})
        return Response(serializer.data[0])


# 管理添加内容分类
class ContentCategoryViewSet(viewsets.ModelViewSet):
    """
    内容分类
    list ：内容分类列表

    """
    serializer_class = ContentCategorySerializer3
    queryset = MagicContentCategory.objects.all()

    @action(['get'], detail=False)
    def categories_list(self, request):
        scheme_categories = MagicContentCategory.objects.filter(parent=None)
        serializer = ContentCategorySerializer(scheme_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['get'], detail=False)
    def categories_level(self, request):
        electron_categories = MagicContentCategory.objects.filter(parent=None)
        serializer = ContentCategorySerializer2(electron_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 网站基本信息
class WebSetViewSet(viewsets.ModelViewSet):
    queryset = WebSite.objects.all()
    serializer_class = WebSiteSerializer
    permission_classes = [IsAuthenticated]
    #    # def create(self, request, *args, **kwargs):
    #     try:
    #         data = request.data
    #         json.dumps(data['source'])
    #         serializer = self.get_serializer(data= data)
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #     except Exception as e:
    #         raise e
    #
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    def list(self, request, *args, **kwargs):
        queryset = self.queryset.order_by('-update_at')
        serializer = self.get_serializer(queryset, many=True)
        print(serializer.data)
        if not serializer.data:
            return Response({"message": "无数据"})
        return Response(serializer.data[0])

    def update(self, request, *args, **kwargs):

        instance = self.get_object()

        data = request.data
        print(data['source'])

        data['source'] = json.dumps(data['source'])
        print(instance.source)
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        redict = serializer.data
        redict['source'] = json.loads(serializer.data['source'])

        print(redict)
        return Response(redict)


# seo
class SEOViewSet(viewsets.ModelViewSet):
    queryset = SEO.objects.all()
    serializer_class = SEOSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.order_by('-update_at')
        serializer = self.get_serializer(queryset, many=True)
        if not serializer.data:
            return Response({"message":"无数据"})
        return Response(serializer.data[0])


# 网站协议
class ProtocolViewSet(viewsets.ModelViewSet):
    """网站协议"""
    queryset = Protocol.objects.all()
    serializer_class = ProtocolSerializer


    def list(self, request, *args, **kwargs):
        queryset = self.queryset.order_by('create_at')
        serializer = self.get_serializer(queryset, many=True)
        if not serializer.data:
            return Response({"message":"无数据"})
        return Response(serializer.data[0])



# 热搜型号
class HotModelViewSet(mixins.CreateModelMixin,mixins.RetrieveModelMixin,mixins.DestroyModelMixin,mixins.ListModelMixin,GenericViewSet):
    """热搜"""
    queryset = Electron.objects.all()
    serializer_class = HotModelSerialier
    def get_queryset(self):
        queryset = Electron.objects.all().filter(isDelete=False)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ElectronSerializer
        # elif self.action == 'list':
        #     return
        return HotModelSerialier

    def create(self, request, *args, **kwargs):
        model_name = request.data['model_name']
        electrons = Electron.objects.get(model_name=model_name)
        electrons.is_hot = True
        electrons.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'], detail=False)
    def hsearch(self, request, *args, **kwargs):
        try:
            model_name = request.query_params['model_name']
            electrons = Electron.objects.filter(model_name__istartswith=model_name,isDelete=False,is_hot= False)
            if electrons is None:
                return Response({'message':'未找到'},status=status.HTTP_200_OK)
            serializer = self.get_serializer(electrons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:

            return Response({'message': '查询失败'}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):        # hot_name = HotModel.objects.filter(is_delete=False)

        hot_name = Electron.objects.filter(is_hot=True)
        serializer = HotModelSerialier(hot_name, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_hot= False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# 内容列表
class MagicContentViewSet(viewsets.ModelViewSet):
    queryset = MagicContent.objects.all()
    serializer_class = MagicContentListSerializer
    def get_serializer_class(self):
        if self.action in ['list','retrieve','update']:
            return MagicContentSerializer
        # elif self.action == 'retrieve' or self.action == 'update':
        return MagicContentListSerializer

class ImageStorageViewSet(mixins.CreateModelMixin,viewsets.GenericViewSet):
    """图片上传接口"""
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    # permission_classes = [IsAuthenticated]


class VideoStorageViewSet(mixins.CreateModelMixin,viewsets.GenericViewSet):

    queryset = Video.objects.all()
    serializer_class = VedioSerializer


class FileStorageViewSet(mixins.CreateModelMixin,viewsets.GenericViewSet):

    queryset = Files.objects.all()
    serializer_class = FilesSerializer



# 后台首页
from django_redis import get_redis_connection
from apps.users.models import User
from apps.electron.models import Electron
from apps.scheme.models import Scheme
from apps.product.models import Product
from apps.order.models import OrderInfo
from django.utils import timezone
from datetime import datetime ,timedelta


class SaveSearchCount(APIView):

    def get(self,request):
        conn = get_redis_connection("default")
        date = timezone.now().strftime('%Y%m%d')
        searches  = conn.get("%s" % date)
        print(searches)
        if not searches:
            conn.setex("%s" % date,7*24*60*60,1)
        pl = conn.pipeline()
        pl.multi()
        pl.incr("%s" % date)

        pl.execute()
        return Response({},status=status.HTTP_200_OK)


class GetSearchCount(APIView):

    def get(self, request):
        conn = get_redis_connection("default")
        date = datetime.now()
        date1 = date - timedelta(days=1)
        date2 = date - timedelta(days=2)
        date3 = date - timedelta(days=3)
        date4 = date - timedelta(days=4)
        date5 = date - timedelta(days=5)
        date6 = date - timedelta(days=6)
        count = conn.get("%s" % date.strftime('%Y%m%d'))
        if not count:
            count = 0
        else:
            count = int(str(count, encoding='utf-8'))
        count1 = conn.get("%s" % date1.strftime('%Y%m%d'))
        if  not count1:
            count1 = 0
        else:
            count1 = int(str(count1, encoding='utf-8'))
        count2 = conn.get("%s" % date2.strftime('%Y%m%d'))

        if  not count2:
            count2 = 0
        else:
            count2 = int(str(count2, encoding='utf-8'))
        count3 = conn.get("%s" % date3.strftime('%Y%m%d'))

        if  not count3:
            count3 = 0
        else:
            count3 = int(str(count3, encoding='utf-8'))
        count4 = conn.get("%s" % date4.strftime('%Y%m%d'))
        if  not count4:
            count4 = 0
        else:
            count4 = int(str(count4, encoding='utf-8'))
        count5 = conn.get("%s" % date5.strftime('%Y%m%d'))
        if  not count5:
            count5 = 0
        else:
            count5 = int(str(count5, encoding='utf-8'))
        count6 = conn.get("%s" % date6.strftime('%Y%m%d'))
        if  not count6:
            count6 = 0
        else:
            count6 = int(str(count6, encoding='utf-8'))

        search_info = [
            {'time':date.strftime('%Y-%m-%d'),
             'num':count,
            },
            {'time':date1.strftime('%Y-%m-%d'),
             'num':count1,
            },
            {'time':date2.strftime('%Y-%m-%d'),
             'num':count2,
            },
            {'time':date3.strftime('%Y-%m-%d'),
             'num':count3,
            },
            {'time':date4.strftime('%Y-%m-%d'),
             'num':count4,
            },
            {'time':date5.strftime('%Y-%m-%d'),
             'num':count5,
            },
            {'time':date6.strftime('%Y-%m-%d'),
             'num':count6,
            },
        ]
        sum = count+count1+count2+count3+count4+count5+count6
        dict1 = {
            'user_count': User.objects.all().count(),
            'avg_search': sum//7
        }

        dict2 = {
            'electron_count': Electron.objects.filter(isDelete=False).count(),
            'scheme_count': Scheme.objects.all().count(),
            'product_count': Product.objects.all().count()
        }

        dict3 = {
            'unpaid_order': OrderInfo.objects.filter(status=1).count(),
            'unsend_order': OrderInfo.objects.filter(status=2).count(),
            'finished_order': OrderInfo.objects.filter(status=4).count(),
        }
        data = {
            'sum':sum,
            'search_info':search_info,
            'info1': dict1,
            'info2': dict2,
            'info3': dict3,

        }
        return Response(data)

class AllHotElectronSchemeProduct(APIView):
    def get(self, request):

        electron = Electron.objects.filter(isDelete=False).order_by('-views')[0:4]
        scheme = Scheme.objects.all().order_by('-views')[0:4]
        product = Product.objects.all().order_by('-views')[0:4]

        serializer = GetHotElectronSchemeProductSerializer({
            'electron':electron,
            'scheme':scheme,
            'product':product,
        })
        return Response(serializer.data)


class LeaveMessageViewSet(viewsets.ModelViewSet):
    """意见或建议"""
    queryset = LeaveMessage.objects.all()
    serializer_class = LeaveMessageSerializer
    pagination_class = Pagination
