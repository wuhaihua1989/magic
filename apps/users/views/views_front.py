from rest_framework.views import APIView

from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import authentication, viewsets, generics, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from apps.users.serializer.serializers_front import *
from django.db import transaction
from rest_framework.decorators import action
from rest_framework_jwt.views import jwt_response_payload_handler

from utils.permission import IsOwnerOrReadOnly


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


class UserAuthorizeView(ObtainJSONWebToken):
    """重写jwt的登陆视图"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # 获取当前用户
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        if serializer.is_valid():
            login_user = serializer.object.get('user') or request.user
            login_user.last_ip = request.META["REMOTE_ADDR"]
            login_user.save()
        # if serializer.is_valid():
            # user = serializer.object.get('user') or request.user
            # response = merge_cart_cookie_to_redis(request, user, response)
        return response


class UserDetailView(RetrieveAPIView):
    """用户中心的详细信息视图类"""

    serializer_class = UserDetailSerializer
    # 设置权限认证类

    permission_classes = [IsAuthenticated]

    def get_object(self):

        return self.request.user


class SMSCodeTokenView(GenericAPIView):
    """通过账号获取临时访问票据[access_token]"""
    # serializer_class = ImageCodeCheckSerializer

    def get(self, request, account):
          
        #  根据提交过来的account获取用户信息
        user = get_user_by_account(account)
        if user is None:
            return Response({"message": "用户不存在！"}, status=status.HTTP_404_NOT_FOUND)

        # 生成access_token
        access_token = user.generate_sms_code_token()

        # 手机号是用户的敏感信息，所以需要处理一下
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)

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
        # 生成重置密码的access_token
        access_token = user.generate_password_token()
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


class UserInfoViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    用户个人中心
    retrieve:
        获取用户信息
    update:
        更新用户信息
    chpassword:
        修改密码
    chmobile:
        修改手机
    """
    queryset = User.objects.all()
    serializer_class = UserInfoSerializer
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "chpassword":
            return UserCheckPasswordSerializer
        elif self.action == "chmobile":
            return UserCheckMobileSerializer
        else:
            return UserInfoSerializer

    def get_object(self):
        return self.request.user

    @action(['post'], detail=True)
    def chpassword(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "修改密码成功!"}, status=status.HTTP_200_OK)

    @action(['post'], detail=True)
    def chmobile(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "修改手机号码成功!"}, status=status.HTTP_200_OK)


class ProfessionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Professions.objects.all()
    serializer_class = ProfessionsSerializer


class IndustryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Industry.objects.all()
    serializer_class = IndustrySerializer


class UserAddressViewSet(viewsets.ModelViewSet):
    """
    个人中心:收货地址
    list:
        获取收货地址
    create:
        添加收货地址
    update:
        更新收货地址
    delete:
        删除收货地址
    default:
        设置地址为默认
    """
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def get_queryset(self):
        return Address.objects.filter(consumer=self.request.user,is_delete=False)

    def get_serializer_class(self):
        if self.action == "default":
            return SetDefaultUserAddressSerializer
        else:
            return UserAddressSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        data['consumer_id'] = request.user.id
        obj = Address.objects.create(**data)
        if obj.is_default == 1:
            self.request.user.default_address = obj
            self.request.user.save()
            all_address = Address.objects.filter(consumer=self.request.user)
            for address in all_address:
                if address.id != obj.id:
                    address.is_default = 0
                    address.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_delete = True
        instance.save()

        return Response({'message': '删除成功'}, status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        try:
            if serializer.data['is_default'] == 1:
                all_address = Address.objects.filter(consumer=self.request.user)
                for address in all_address:
                    if address.id != int(serializer.data['id']):
                        address.is_default = 0
                        address.save()
                    else:
                        self.request.user.default_address = address
                        self.request.user.save()
        except Exception as e:
            return Response({"fail": "设置为默认地址出错", "error": e}, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['post'], detail=True)
    def default(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        try:
            if serializer.data['is_default'] == 1:
                all_address = Address.objects.filter(consumer=self.request.user)
                for address in all_address:
                    if address.id != int(serializer.data['id']):
                        address.is_default = 0
                        address.save()
                    else:
                        self.request.user.default_address = address
                        self.request.user.save()
        except Exception as e:
            return Response({"fail": "设置为默认地址出错", "error": e}, status=status.HTTP_200_OK)
        return Response({"success": "设置为默认地址成功"}, status=status.HTTP_200_OK)


# --------------后台管理界面逻辑代码--------------


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
            print(user)
        except User.DoesNotExist:
            return Response({"error": "不存在的对象"}, status=status.HTTP_400_BAD_REQUEST)
        response = Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return response
