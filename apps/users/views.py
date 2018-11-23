from rest_framework.views import APIView
from .models import *
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView, RetrieveAPIView

from apps.verifications.serializers import ImageCodeCheckSerializer
from rest_framework import status, mixins
from .utils import get_user_by_account
from rest_framework.permissions import IsAuthenticated
import re
from rest_framework import (status, authentication, permissions, filters, viewsets, routers,generics)
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from .serializers import *
from django.db import transaction
from rest_framework.decorators import action


# ----------客户界面逻辑代码---------------
class UserNameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        """
        获取指定用户名数量
        """
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """
    手机号数量
    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)


class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """通过账号获取临时访问票据[access_token]"""
    serializer_class = ImageCodeCheckSerializer

    def get(self, request, account):
        """
        :account 手机号码或者账号名
        :return: access_token 或者 None
        """
        # 1. 校验图形验证码是否正确
        serializer = self.get_serializer(data=request.query_params)  # request.query_params 地址栏中?号后面的查询字符串
        serializer.is_valid(raise_exception=True)

        # 2. 根据提交过来的account获取用户信息
        user = get_user_by_account(account)
        if user is None:
            return Response({"message": "用户不存在！"}, status=status.HTTP_404_NOT_FOUND)

        # 3. 生成access_token
        access_token = user.generate_sms_code_token()

        # 手机号是用户的敏感信息，所以需要处理一下
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)

        # 4. 返回响应数据
        return Response({
            'mobile': mobile,
            'access_token': access_token
        })


class PasswordTokenView(GenericAPIView):
    """获取重置密码的access_token"""
    serializer_class = CheckSMSCodeSerializer

    def get(self, request, account):
        serializer = self.get_serializer(data=request.query_params)  # request.query_params 地址栏中?号后面的查询字符串
        serializer.is_valid(raise_exception=True)

        # 获取之前在序列化器中的用户对象
        user = serializer.user

        # 3. 生成重置密码的access_token
        access_token = user.generate_password_token()

        # 4. 响应，返回user_id和access_token
        return Response({
            'user_id': user.id,
            'access_token': access_token
        })


class PasswordView(UpdateAPIView):
    """修改和生成密码"""
    queryset = User.objects.all()  # UpdateModelMixin 要求查询所有用户，让通过pk指定某一个用户的数据更新
    serializer_class = CheckPasswordTokenSerializer

    def post(self, request, pk):
        """重置密码"""
        # 1. 调用序列化器验证数据进行校验和更新数据
        return self.update(request, pk)

    def put(self, request, pk):  # 修改密码
        pass


class UserDetailView(RetrieveAPIView):
    """用户中心的详细信息视图类"""
    # 这里使用序列化的作用仅仅是设置返回的字段而已
    serializer_class = UserDetailSerializer
    # 设置权限认证类
    # IsAuthenticated 表示必须通过登陆认证以后才能访问
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # 返回的就是当前视图对象中，由jwt认证完成以后提供的用户模型
        return self.request.user


# --------------后台管理界面逻辑代码--------------



# 用户组（角色）
class GroupViewSet(viewsets.ModelViewSet):
    """
       retrieve:
           角色详情
       list:
           后台角色列表
       create:
           新增角色
       delete:
           删除角色
       update:
           更新角色
       """
    queryset = Group.objects.all()
    serializer_class = GroupListSerializer
    authentication_classes = (JSONWebTokenAuthentication, authentication.SessionAuthentication)

    def update(self, request, *args, **kwargs):
        """修改角色菜单"""
        try:
            with transaction.atomic():
                group = Group.objects.get(id=request.data['group']['id'])
                group.name = request.data['group']['name']
                group.save()

                # 新的集合数组
                new_menus = request.data['menus']

                role_menus = RoleMenu.objects.filter(role=group)
                old_menus = [role_menu.menu.id for role_menu in role_menus]
                # 获取差集
                # list(set(b).difference(set(a))) # b中有而a中没有的 删除
                remove_menus = list(set(old_menus).difference(set(new_menus)))
                for menu_id in remove_menus:
                    menu = Menu.objects.get(id=menu_id)
                    role_menu = RoleMenu.objects.get(menu=menu, role=group)
                    role_menu.delete()

                # list(set(a).difference(set(b))) # a中有而b中没有的 新增
                add_menus = list(set(new_menus).difference(set(old_menus)))
                role_menus = []
                for menu_id in add_menus:
                    menu = Menu.objects.get(id=menu_id)
                    role_menus.append(RoleMenu(role=group, menu=menu))
                RoleMenu.objects.bulk_create(role_menus)
                return Response({'message': 'ok'}, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({'message': '不存在的对象'}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """
        获取角色详情
        """
        # get 方式传参数
        group_id = kwargs.get("pk", None)
        # data = {"message": "ok"}
        data = {}
        try:
            group = Group.objects.get(pk=group_id)
            group_serializer = GroupListSerializer(group)
            role_menus = RoleMenu.objects.filter(role=group)
            menus = [role_menu.menu for role_menu in role_menus]
            menu_serializer = MenuCreateSerializer(menus, many=True)
            data['group'] = group_serializer.data
            data['menus'] = menu_serializer.data
            # return Response(data, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({'pk': group_id, "error": "不存在的对象"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """新增角色"""
        try:
            with transaction.atomic():
                role = Group(name=request.data["group"]['name'])
                role.save()
                menus = request.data['menus']
                # 新增用户对应的菜单
                for menu_id in menus:
                    menu = Menu.objects.get(id=menu_id)
                    role = Group.objects.get(name=role.name)
                    role_menu = RoleMenu(menu=menu, role=role)
                    role_menu.save()
                return Response({'message': 'ok'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'message': 'error'}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        """
        # 动态选择序列化方式
        # 1. UserRegSerializer (用户注册)， 只返回username 和 mobile
        # 2. UserSerializer (用户中心) 返回用户详细数据
        :return:
        """
        if self.action == 'list':
            return GroupListSerializer
        elif self.action in ['create', 'update', 'retrieve', 'partial_update']:
            return GroupCreateSerializer
        return GroupSerializer

        # def get_permissions(self):
        #     return [permissions.IsAuthenticated() or permissions.IsAdminUser()]

        # def get_permissions(self):
        #     return [permissions.IsAuthenticated() or permissions.IsAdminUser()]


# 权限
class PermissionViewSet(generics.ListCreateAPIView, viewsets.GenericViewSet):
    """
        list:
           权限列表
        create:
           权限新增
    """

    queryset = Permission.objects.all()
    serializer_class = PermissionListSerializer

    # def create(self, request, *args, **kwargs):
    #     # print(request.data)
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response({'message': "ok"}, status=status.HTTP_200_OK)
    #     else:
    #         return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = Permission.objects.filter(content_type_id='57')
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return PermissionListSerializer
        else:
            return PermissionCreateSerializer

            # def get_permissions(self):
            #     return [permissions.IsAuthenticated() or permissions.IsAdminUser()]


# 菜单
class MenuViewSet(generics.ListCreateAPIView, viewsets.GenericViewSet):
    """
        list:
           菜单列表(嵌套子类)
        menu_list:
            菜单列表(无嵌套子类)
        create:
           菜单新增
    """
    queryset = Menu.objects.all()
    serializer_class = MenuListSerializer

    # def list(self, request, *args, **kwargs):
    #     print(request)
    @action(['get'], detail=False)
    def menu_list(self, request):
        menus = Menu.objects.all()
        serializer = MenuCreateSerializer(menus, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def list(self, request, *args, **kwargs):
    #     menus = Menu.objects.filter(parent=None)
    #     serializer = self.get_serializer(menus, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == 'list':
            return MenuListSerializer
        else:
            return MenuCreateSerializer

    def get_queryset(self):
        return Menu.objects.filter(parent=None)
