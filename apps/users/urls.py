from django.conf.urls import (include, url)
from apps.users.views import *
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token
from apps.users.views import views_back, views_front
from apps.users.views.views_back import *
from magic.settings import PREFIX, PREFIX_BACK
from apps.users.views import *

from apps.verifications.views import SmsCodeViewset


router = routers.DefaultRouter()
router.register(PREFIX_BACK + 'groups', views_back.GroupViewSet)
router.register(PREFIX_BACK + 'permissions', views_back.PermissionViewSet)
router.register(PREFIX_BACK + 'menus', views_back.MenuViewSet)
router.register(PREFIX_BACK + 'users/back', views_back.UserBackView)
router.register(PREFIX_BACK + 'users/members', UserMemberView)
# router.register('ic/user/address', views_front.AddressViewSet, base_name='addresses')

# 前台url
router.register(PREFIX_BACK + 'users/info', views_front.UserInfoViewSet, base_name="user_info")   # 个人中心
router.register(PREFIX_BACK + 'users/address', views_front.UserAddressViewSet, base_name="user_address")  # 收货地址
router.register(PREFIX_BACK + 'code', SmsCodeViewset, base_name="send_code")  # 获取短信验证码
router.register(PREFIX_BACK + 'professions', views_front.ProfessionsViewSet, base_name="professions")  # 获取职业
router.register(PREFIX_BACK + 'industry', views_front.IndustryViewSet, base_name="industry")  # 获取行业

# index = IndexViewSet.as_view({'get': 'list'})
user_back_login = views_front.UserViewSet.as_view()
urlpatterns = [
    url(r'', include(router.urls)),
    url(r'^ic/usernames/(?P<username>\w{5,20})/count/$', views_front.UserNameCountView.as_view()),
    url(r'^ic/mobiles/(?P<mobile>1[345789]\d{9})/count/$', views_front.MobileCountView.as_view()),
    url(r'^ic/users/$', views_front.UserView.as_view()),
    url(r'^ic/authorizations/$', views_front.UserAuthorizeView.as_view(), name='authorizations'),  # 登陆视图
    url(r"^ic/accounts/(?P<account>\w{5,20})/sms/token/$", views_front.SMSCodeTokenView.as_view()),
    url(r"^ic/accounts/(?P<account>\w{5,20})/password/token/$", views_front.PasswordTokenView.as_view()),
    url(r"^ic/users/(?P<pk>\d+)/password/$", views_front.PasswordView.as_view()),
    url(r"^ic/user/detail$", views_front.UserDetailView.as_view()),
    url(r'^' + PREFIX_BACK + 'backenduser/login/', user_back_login, name='后台用户登陆'),
    url(r'^' + PREFIX_BACK + 'index/', views_front.IndexViewSet.as_view(), name='后台用户首页'),

]
