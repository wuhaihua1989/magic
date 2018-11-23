from rest_framework import serializers
import re
from django_redis import get_redis_connection
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework_jwt.settings import api_settings
from django.core.mail import send_mail
from django.conf import settings

from .models import *
from .utils import get_user_by_account
# from celery_tasks.email.tasks import send_verify_email






class CreateUserSerializer(serializers.ModelSerializer):
    """
    创建用户序列化器
    """
    password2 = serializers.CharField(label='确认密码', required=True, allow_null=False, allow_blank=False, write_only=True)
    sms_code = serializers.CharField(label='短信验证码', required=True, allow_null=False, allow_blank=False, write_only=True)
    allow = serializers.CharField(label='同意协议', required=True, allow_null=False, allow_blank=False, write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)  # 增加token字段

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[345789]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']

        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        创建用户
        """
        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        # User.objects.create()
        user = super().create(validated_data)

        # 调用django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 调用jwt生成一个token，保存到用户模型中

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER # 载荷相关配置
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER   # token配置

        # 生成载荷
        payload = jwt_payload_handler(user)
        # 生成token
        token = jwt_encode_handler(payload)

        # 把token放到user模型对象
        user.token = token

        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow',"token")
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }


class CheckSMSCodeSerializer(serializers.Serializer):
    """校验短信验证码的序列化器"""
    sms_code = serializers.CharField(min_length=6, max_length=6)

    def validate_sms_code(self,value):

        # 获取用户账号名
        account = self.context['view'].kwargs['account']

        # 获取user
        user = get_user_by_account(account)
        if user is None:
            raise serializers.ValidationError('用户不存在')

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')

        if value != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        # 把序列化器中的数据通过属性传递到视图中
        self.user = user

        return value

class CheckPasswordTokenSerializer(serializers.ModelSerializer):
    """
    重置密码序列化器
    """
    password2 = serializers.CharField(label='确认密码',  write_only=True)
    access_token = serializers.CharField(label='重置密码的access_token',  write_only=True)

    def validate(self,attrs):
        """
        校验数据
        """
        # 判断两次密码
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 1. 校验access_token
        allow = User.check_set_password_token(attrs['access_token'], self.context['view'].kwargs['pk'])
        if not allow:
            raise serializers.ValidationError('无效的access token')

        return attrs

    def update(self,instance, validated_data):
        """
        更新密码
        :param instance: 根据pk对应的User模型对象
        :param validated_data: 验证完成以后的数据
        :return:
        """
        # Django默认的User认证模型会提供set_password密码加密的方法
        instance.set_password(validated_data["password"])
        instance.save()
        return instance


    # 生成模型
    class Meta:
        model = User
        fields = ('id', 'password', 'password2', 'access_token')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # 这里就是指定返回什么数据给前端
        fields = ('id', 'username', 'mobile')








# 用户组（角色）列表序列化
class GroupListSerializer(serializers.ModelSerializer):
    """用户组（角色）列表"""
    permissions_name = serializers.SerializerMethodField()  # 自定义字段的申明

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions_name']

    def get_permissions_name(self, obj):  # 自定义的字段实现

        permission_names = map(lambda role_menu: role_menu.menu.cname, list(RoleMenu.objects.filter(role=obj)))
        # print(permission_names)
         # for permission in obj.permissions.all()
        return ",".join(permission_names)


# 新增用户组（角色）序列化
class GroupSerializer(serializers.ModelSerializer):
    """新增用户组（角色）"""

    def __init__(self, *args, **kwargs):
        """
        定义用户的列表
        """
        super(GroupSerializer, self).__init__(*args, **kwargs)
        # self.fields['id'] = serializers.IntegerField(label='角色ID', help_text='角色ID', required=True, allow_null=False, )
        self.fields['name'] = serializers.CharField(label='角色名称', help_text='角色名称', required=False)
        self.fields['menus'] = serializers.PrimaryKeyRelatedField(many=True, queryset=Menu.objects.all(), required=False, help_text='菜单', label='菜单')

    class Meta:
        model = Group
        fields = '__all__'


class GroupCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(GroupCreateSerializer, self).__init__(*args, **kwargs)
        # self.fields['id'] = serializers.IntegerField(label='角色ID', help_text='角色ID', required=True, allow_null=False, )
        self.fields['name'] = serializers.CharField(label='角色名称', help_text='角色名称', required=False)
        self.fields['menus'] = serializers.PrimaryKeyRelatedField(many=True, queryset=Menu.objects.all(), required=False, help_text='菜单', label='菜单')

    class Meta:
        model = Group
        fields = ['name']
        # read_only_fields = ('menus',)

        # 对象级别的验证

    # def create(self, validated_data):
    #     validated_data.pop('menus')
    #     return super(GroupCreateSerializer, self).create(validated_data)


# 一级菜单
class MenuCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'


# 菜单
class MenuListSerializer(serializers.ModelSerializer):
    children = MenuCreateSerializer(many=True)

    class Meta:
        model = Menu
        fields = '__all__'


# 返回自定义权限列表
class PermissionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


# 新增权限序列化
class PermissionCreateSerializer(serializers.ModelSerializer):
    content_type = PrimaryKeyRelatedField(queryset=ContentType.objects.filter(id=57), required=True, label='权限类型', help_text='权限类型')

    class Meta:
        model = Permission
        fields = "__all__"











