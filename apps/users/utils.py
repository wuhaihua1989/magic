from django.contrib.auth.backends import ModelBackend
import re

from apps.users.models import User

def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    :param token: 生成的token令牌
    :param user: 前面验证通过以后得到的用户模型对象
    :param request: 本次用户提交请求信息
    :return: json，前端希望提供的数据
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }

def get_user_by_account(account):
    """
    根据手机号或者用户名获取Usser模型对象
    :param account: 手机号/账号名
    :return: User对象/ None
    """
    try:
        if re.match('^1[345789]\d{9}$', account):
            # 帐号为手机号
            user = User.objects.get(mobile=account)
        else:
            # 帐号为用户名
            user = User.objects.get(username=account)

    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义用户名或手机号认证
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)
        # 判断是否可以通过账号信息获取用户对象，并且密码正确
        print('============用户认证=========')
        if user is not None and user.check_password(password):
            return user