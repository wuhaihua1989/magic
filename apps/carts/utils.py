import pickle
import base64
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    合并请求用户的购物车数据，将未登录保存在cookie里的保存到redis中
    :param request: 用户的请求对象
    :param user: 当前登录的用户
    :param response: 响应对象，用于清楚购物车cookie
    :return:
    """
    cookie_cart = request.COOKIES.get('carts')
    if cookie_cart is not None:
        return response

    cookie_cart = pickle.loads(base64.b64decode(cookie_cart.encode()))
    redis_conn = get_redis_connection('carts')
    pl = redis_conn.pipeline()
    for electron_id, data in cookie_cart.items():
        # 修改商品数量
        pl.hset("cart_%s" % user.id, electron_id, data['count'])
    pl.execute()

    # 4. 清除cookie中的购物车
    response.delete_cookie('carts')

    return response