from rest_framework import serializers, status
import re
from datetime import datetime
from datetime import timedelta
from rest_framework.response import Response
from django_redis import get_redis_connection
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework_jwt.compat import PasswordField
from rest_framework_jwt.settings import api_settings
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.validators import UniqueValidator
from apps.users.models import *
from apps.users.utils import get_user_by_account
from rest_framework_jwt.compat import get_username_field, PasswordField
from rest_framework_jwt.serializers import jwt_encode_handler, jwt_payload_handler
from rest_framework_jwt import compat
from django.utils.translation import ugettext as _
from django.contrib.auth import (get_user_model, authenticate)

from magic.settings import REGEX_MOBILE


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
        if not re.match(REGEX_MOBILE, value):
            raise serializers.ValidationError('手机号格式错误')
        # queryset=User.objects.get(value)
        # if queryset:
        #     raise serializers.ValidationError('手机已被注册')
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

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 载荷相关配置
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # token配置

        # 生成载荷
        payload = jwt_payload_handler(user)
        # 生成token
        token = jwt_encode_handler(payload)

        # 把token放到user模型对象
        user.token = token

        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', "token")
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 6,
                'max_length': 18,
                'error_messages': {
                    'min_length': '仅允许6-18个字符的用户名',
                    'max_length': '仅允许6-18个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 6,
                'max_length': 22,
                'error_messages': {
                    'min_length': '仅允许6-22个字符的密码',
                    'max_length': '仅允许6-22个字符的密码',
                }
            }
        }


class CheckSMSCodeSerializer(serializers.Serializer):
    """校验短信验证码的序列化器"""
    sms_code = serializers.CharField(min_length=6, max_length=6)

    def validate_sms_code(self, value):

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
    password2 = serializers.CharField(label='确认密码', write_only=True)
    access_token = serializers.CharField(label='重置密码的access_token', write_only=True)

    def validate(self, attrs):
        """
        校验数据
        """
        # 判断两次密码
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        #校验access_token
        allow = User.check_set_password_token(attrs['access_token'], self.context['view'].kwargs['pk'])
        if not allow:
            raise serializers.ValidationError('无效的access token')

        return attrs

    def update(self, instance, validated_data):
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
                'min_length': 6,
                'max_length': 22,
                'error_messages': {
                    'min_length': '仅允许6-22个字符的密码',
                    'max_length': '仅允许6-22个字符的密码',
                }
            }
        }


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # 这里就是指定返回什么数据给前端
        fields = ('id', 'username', 'mobile')


# 用户模型序列化
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = ['username', 'mobile', 'rel_name', 'email', 'gender', 'profession', 'industry', 'company_name', 'company_tel_number', 'company_fax_number', 'company_tax_number', 'company_address']
        exclude = ['password']  # 与 fields 功效 相反
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
        self.fields['menus'] = serializers.PrimaryKeyRelatedField(many=True, queryset=Menu.objects.all(),
                                                                  required=False, help_text='菜单', label='菜单')

    class Meta:
        model = Group
        fields = '__all__'


class GroupCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(GroupCreateSerializer, self).__init__(*args, **kwargs)
        # self.fields['id'] = serializers.IntegerField(label='角色ID', help_text='角色ID', required=True, allow_null=False, )
        self.fields['name'] = serializers.CharField(label='角色名称', help_text='角色名称', required=False)
        self.fields['menus'] = serializers.PrimaryKeyRelatedField(many=True, queryset=Menu.objects.all(),
                                                                  required=False, help_text='菜单', label='菜单')

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
    content_type = PrimaryKeyRelatedField(queryset=ContentType.objects.filter(id=57), required=True, label='权限类型',
                                          help_text='权限类型')

    class Meta:
        model = Permission
        fields = "__all__"


class UserLoginSerializer(compat.Serializer):
    """
        序列化验证一个用户名和密码
        返回一个可以被用来验证接口的 JSON Web Token
    """

    def __init__(self, *args, **kwargs):
        """
        Dynamically add the USERNAME_FIELD to self.fields.
        """
        super(UserLoginSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField(label='用户名', help_text='用户名')
        self.fields['password'] = PasswordField(write_only=True, label='用户密码', help_text='用户密码')

    @property
    def username_field(self):
        return get_username_field()

    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }
        if all(credentials.values()):
            user = authenticate(**credentials)
            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)

                payload = jwt_payload_handler(user)

                return {
                    'token': jwt_encode_handler(payload),
                    'user': user
                }
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)


# 会员中心:收货地址
class UserAddressSerializer(serializers.ModelSerializer):
    """用户收货地址序列化"""
    province = serializers.CharField(label="省份", required=True, error_messages={"required": "省份不能为空"})
    city = serializers.CharField(label="城市", required=True, error_messages={"required": "城市不能为空"})
    district = serializers.CharField(label="区域", required=True, error_messages={"required": "区域不能为空"})
    address = serializers.CharField(label="详细地址", required=True, error_messages={"required": "详细地址不能为空"})

    consumer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Address
        fields = ["id", "consumer", "signer_name", "signer_mobile", "province", "city", "district", "address", "is_default"]


class UserDefaultAddressSerializer(serializers.ModelSerializer):
    """用户默认收货地址序列化"""
    consumer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Address
        fields = ["consumer",  "province", "city", "district", "address"]


class SetDefaultUserAddressSerializer(serializers.ModelSerializer):
    """设为默认地址序列化"""
    consumer = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Address
        fields = ["id", "consumer", "is_default"]


# 会员中心:个人中心
class ProfessionsSerializer(serializers.ModelSerializer):
    """职业序列化"""
    class Meta:
        model = Professions
        fields = ["id", "name"]


class IndustrySerializer(serializers.ModelSerializer):
    """行业序列化"""
    class Meta:
        model = Industry
        fields = ["id", "name"]


class UserInfoSerializer(serializers.ModelSerializer):
    """个人中心序列化"""
    last_login = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    last_ip = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    icon = serializers.CharField()
    is_member = serializers.BooleanField(read_only=True)
    default_address = UserDefaultAddressSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'last_login', 'last_ip', 'username', 'icon', 'is_member', 'mobile', 'email', 'rel_name',
                  'gender', 'profession', 'industry', 'qq', 'company_name', 'company_tel_number', 'company_fax_number',
                  'company_address', 'company_tax_number', 'bank_name', 'bank_account', 'signer_name', 'signer_mobile',
                  'send_address', "default_address"]


class UserCheckPasswordSerializer(serializers.ModelSerializer):
    """
    用户修改密码序列化器
    """
    password = serializers.CharField(required=True, write_only=True, max_length=22, min_length=6, label="旧密码",
                                     error_messages={"blank": "请输入旧密码", "required": "请输入旧密码",
                                                     "max_length": "仅允许6-22个字符的密码",
                                                     "min_length": "仅允许6-22个字符的密码"})
    password1 = serializers.CharField(required=True, write_only=True, max_length=22, min_length=6, label="新密码",
                                      error_messages={"blank": "请输入新密码", "required": "请输入新密码",
                                                      "max_length": "仅允许6-22个字符的密码",
                                                      "min_length": "仅允许6-22个字符的密码"})
    password2 = serializers.CharField(required=True, write_only=True, max_length=22, min_length=6, label="确认新密码",
                                      error_messages={"blank": "请再次输入新密码", "required": "请再次输入新密码",
                                                      "max_length": "仅允许6-22个字符的密码"})

    def validate(self, attrs):
        """
        校验数据
        """
        # 验证旧密码是否正确
        user = self.context["request"].user
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError({"error": "旧密码输入错误!"})

        # 新密码不能与旧密码相同
        if user.check_password(attrs["password1"]):
            raise serializers.ValidationError({"error": "新密码与旧密码相同!"})

        # 判断两次密码
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"error": "两次密码不一致!"})

        attrs["password"] = attrs['password2']

        del attrs['password1']
        del attrs['password2']

        return attrs

    def update(self, instance, validated_data):
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

    class Meta:
        model = User
        fields = ('id', 'password', 'password1', 'password2')


class UserCheckMobileSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(required=True, write_only=True, max_length=6, min_length=6, label="短信验证码")
    mobile = serializers.CharField(max_length=11, required=True, label="手机号码")

    def validate_mobile(self, mobile):
        """
        验证手机号码
        :param data:
        :return:
        """
        # 手机是否存在
        if User.objects.filter(mobile=mobile).count():
            raise serializers.ValidationError("手机号码已经存在")
        # 验证手机号码是否合法
        if not re.match(REGEX_MOBILE, mobile):
            raise serializers.ValidationError("手机号码非法")

        return mobile

    def validate_sms_code(self, sms_code):
        """
        验证短信验证码
        :param data:
        :return:
        """
        mobile = self.context["request"].data["mobile"]

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')

        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return sms_code

    def validate(self, attrs):
        del attrs["sms_code"]
        return attrs

    class Meta:
        model = User
        fields = ('mobile', 'sms_code')


