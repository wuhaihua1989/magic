from rest_framework import serializers

from rest_framework.relations import PrimaryKeyRelatedField

from apps.users.models import *
from rest_framework.validators import UniqueValidator
from rest_framework_jwt.compat import get_username_field, PasswordField
from rest_framework_jwt.serializers import jwt_encode_handler, jwt_payload_handler
from rest_framework_jwt import compat
from django.utils.translation import ugettext as _
from django.contrib.auth import (get_user_model, authenticate)



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


# 用户列表序列化
class UserMemberListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        # fields 过滤查询结果的显示字段
        fields = ['id', 'username', 'company_name', 'is_member', 'date_joined']

class UserBackDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['rel_name', 'username', 'mobile','email', 'gender', 'profession', 'industry', 'qq', 'company_name', 'company_tel_number', 'company_address', 'icon']

class UserRegBackSerializer(serializers.ModelSerializer):
    password = PasswordField(max_length=100, label='登陆密码', help_text='用户密码', required=True)
    # 验证用户名是否存在
    username = serializers.CharField(label='用户名', help_text='用户名', required=True, allow_blank=False,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message='用户名已经存在')])
    rel_name = serializers.CharField(label='管理员姓名', help_text='管理员姓名', required=False, allow_null=True)
    groups = serializers.PrimaryKeyRelatedField(help_text='角色', many=True, queryset=Group.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'groups', 'rel_name', 'mobile']
        # fields = '__all__'

    def create(self, validated_data):
        user = super(UserRegBackSerializer, self).create(validated_data=validated_data)
        user.set_password(validated_data['password'])
        user.is_staff = True
        user.save()
        return user


# 用户后列表用户台更新
class UserUpdateBackSerializer(serializers.ModelSerializer):
    password = PasswordField(max_length=100, label='登陆密码', help_text='用户密码', required=False)
    # 验证用户名是否存在
    username = serializers.CharField(label='用户名', help_text='用户名', required=True, allow_blank=False)
    rel_name = serializers.CharField(label='管理员姓名', help_text='管理员姓名', required=False, allow_null=True)
    groups = serializers.PrimaryKeyRelatedField(help_text='角色', many=True, queryset=Group.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'groups', 'rel_name', 'mobile']
        # fields = '__all__'

    def update_user(self, instance):
        # instance = UserProfile.objects.get(id=self.initial_data['id'])
        if self.initial_data['password'] != "":
            instance.set_password(self.initial_data['password'])
        instance.username = self.initial_data['username']
        instance.rel_name = self.initial_data['rel_name']
        instance.groups.set(self.initial_data['groups'])
        instance.mobile = self.initial_data['mobile']
        instance.save()

# 用户注册序列化
class UserRegSerializer(serializers.ModelSerializer):
    """用户注册"""
    # UserProfile 中 没有 code 字段， 这里需要自定义一个 code 字段
    code = serializers.CharField(required=True, write_only=True, max_length=4, min_length=4, label='验证码',
                                 error_messages={
                                     'blank': '请输入验证码',
                                     'required': '请输入验证码',
                                     'max_length': '验证码格式错误',
                                     'min_length': '验证码格式错误'
                                 }, help_text='验证码')
    # 验证用户名是否存在
    username = serializers.CharField(label='用户名', help_text='用户名', required=True, allow_blank=False,
                                     validators=[UniqueValidator(queryset=User.objects.all(), message='用户名已经存在')])

    # 输入密码的时候不显示铭文
    password = serializers.CharField(style={'input_type': 'password'}, label="密码", help_text='密码', required=True, write_only=True)



    # 对象级别的验证
    def validate(self, attrs):
        # code 是自己添加的验证字段，数据库中并没有，验证完之后 删除
        del attrs['code']
        return attrs

    def create(self, validated_data):
        user = super(UserRegSerializer, self).create(validated_data=validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    class Meta:
        model = User
        fields = ['username', 'code', 'mobile', 'password']


# 管理后台用户列表
class UserListBackSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField(help_text='角色')  # 自定义字段的申明

    class Meta:
        model = User
        fields = ['id', 'username', 'group_name', 'mobile']
        # fields = ['username', 'groups', 'mobile']

    def get_group_name(self, obj):  # 自定义的字段实现
        group_names = map(lambda group: group.name, list(obj.groups.all()))
        return ",".join(group_names)