from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework import mixins
from django.http import Http404
from rest_framework import status, authentication, viewsets, generics
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from apps.users.serializer.serializers_back import *
from django.db import transaction
from rest_framework.decorators import action
from rest_framework_jwt.views import jwt_response_payload_handler
from apps.users.pagination import UserPagination


class UserViewSet(ObtainJSONWebToken):
    """用户模块接口"""

    # authentication_classes = (JSONWebTokenAuthentication, authentication.SessionAuthentication)
# 后台用户登录

    def post(self, request, *args, **kwargs):
        """后台用户登录"""
        serializer = self.get_serializer(data=request.data)
        print(request.data)
        # self.get_object()
        if serializer.is_valid():

            user = serializer.object.get('user') or request.user
            print(user)
            token = serializer.object.get('token')
            print(token)
            # 返回前台登陆数据
            response_data = jwt_response_payload_handler(token, user, request)
            response_data['user'] = UserSerializer(user).data

            # 获取用户菜单
            if user.is_superuser:
                menus = Menu.objects.all()
                menus_serializer = MenuCreateSerializer(menus, many=True)
                response_data['menus'] = menus_serializer.data
            else:
                groups = Group.objects.filter(user=user)
                menus = set()
                for group in groups:
                    role_menus = RoleMenu.objects.filter(role=group)
                    for role_menu in role_menus:
                        menus.add(role_menu.menu)
                if menus:
                    menus_serializer = MenuCreateSerializer(menus, many=True)
                    response_data['menus'] = menus_serializer.data
                else:
                    response_data['menus'] = []
            login_user = serializer.object.get('user') or request.user
            login_user.last_ip = request.META["REMOTE_ADDR"]
            login_user.save()
            response = Response(response_data)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class IndexViewSet(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """首页接口"""
        try:
            user = User.objects.get(username=request.user.username)
        except User.DoesNotExist:
            return Response({"error": "不存在的对象"}, status=status.HTTP_400_BAD_REQUEST)
        response = Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return response


# 后端（后台用户接口）
class UserBackView(viewsets.ModelViewSet):
    """
        后台用户模块接口

        retrieve:
           后台用户详情
        list:
           后台用户列表
        create:
           后台用户新增
        delete:
           后台用户删除
        update:
           后台用户更新
    """
    serializer_class = UserRegSerializer
    queryset = User.objects.filter(is_staff=True, is_active=True)
    authentication_classes = (JSONWebTokenAuthentication, authentication.SessionAuthentication)

    def get_serializer_class(self):
        if self.action in ['create']:
            return UserRegBackSerializer
        elif self.action in ["update", 'partial_update']:
            return UserUpdateBackSerializer
        elif self.action == "list":
            return UserListBackSerializer
        return UserSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        return serializer.update_user(instance)

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.is_staff = True
        instance.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def get_object(self):
        try:
            return User.objects.get(id=self.kwargs[self.lookup_field], is_active=True, is_staff=True)
        except User.DoesNotExist:
            raise Http404('不存在的对象.')


class UserMemberView(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
        retrieve:
           后台会员用户详情
        list:
           后台会员用户列表
        create:
           后台会员用户新增
        delete:
           后台会员用户删除
        update:
           后台会员用户更新
    """
    serializer_class = UserMemberListSerializer
    queryset = User.objects.all()
    authentication_classes = (JSONWebTokenAuthentication, authentication.SessionAuthentication)
    # filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username', 'company_name')
    ordering_fields = ('date_joined',)
    pagination_class = UserPagination
    
    def get_queryset(self):
        queryset = User.objects.filter(is_superuser=False,is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserBackDetailSerializer
        return UserMemberListSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def get_object(self):
        try:
            return User.objects.get(id=self.kwargs[self.lookup_field], is_active=True, is_staff=False)
        except User.DoesNotExist:
            raise Http404('不存在的对象.')
