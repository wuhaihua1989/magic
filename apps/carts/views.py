from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated

from .serializers import CartSerializer,  CartDeleteSerializer
from apps.electron.models import Electron
from apps.electron.pagination import Pagination

# Create your views here.


class CartView(APIView):
    """购物车视图类"""
    pagination_class = Pagination
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        添加购物车
        """
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        electron_id = serializer.data.get('electron_id')
        count = serializer.data.get('count')

        user = request.user
        # 用户已登录，在redis中保存
        redis_conn = get_redis_connection('carts')
        pl = redis_conn.pipeline()
        # 记录购物车商品数量
        pl.hincrby('cart_%s' % user.id, electron_id, count)
        pl.sadd('cart_selected_%s' % user.id, electron_id)
        pl.execute()
        return Response({"message": '添加成功'}, status=status.HTTP_200_OK)

    def get(self, request):
        """
        查看购物车数据
        """
        user = request.user
        redis_conn = get_redis_connection('carts')
        # hgetall 获取指定名称的hash表中所有的键值对
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart = {}
        queryset = []
        for electron_id, count in redis_cart.items():
            cart[int(electron_id)] = {
                "count": int(count),
            }
        electrons = Electron.objects.filter(id__in=cart.keys())
        for electron in electrons:
            electron.count = cart[electron.id]['count']
            electron.amount = int(electron.count) * electron.platform_price
            electron_data = {
                'id': electron.id,
                'count': electron.count,
                'model_name': electron.model_name,
                'images': electron.images,
                'platform_price': electron.platform_price,
                'factory': electron.factory,
                'total_price': electron.amount,
            }
            queryset.append(electron_data)
        return Response(queryset)

    def put(self, request):
        # 校验数据
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        electron_id = serializer.data.get('electron_id')
        count = serializer.data.get('count')

        user = request.user
        # 用户已登录，在redis中保存
        redis_conn = get_redis_connection('carts')
        pl = redis_conn.pipeline()
        # hset 修改指定hash表中对应的键的值
        pl.hset('cart_%s' % user.id, electron_id, count)
        pl.execute()
        return Response(serializer.data)

    def delete(self, request):
        """
        删除购物车数据
        """
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        electron_id = serializer.data['electron_id']

        user = request.user
        # 用户已登录，在redis中删除购物车商品
        redis_conn = get_redis_connection('carts')
        pl = redis_conn.pipeline()
        # 购物车商品信息
        # hdel 删除hash表中指定的键值对
        pl.hdel('cart_%s' % user.id, electron_id)
        pl.execute()
        return Response(status=status.HTTP_204_NO_CONTENT)



