"""magic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.documentation import include_docs_urls
# 媒体文件想要通过ip地址访问到静态文件要做如下配置
from django.views.static import serve  # 导入
from django.conf import settings
from django.views.generic import TemplateView
# from rest_framework import routers
# from rest_framework.authtoken import views
# from apps.user.views import GroupViewSet
# from apps.user.routers import CustomReadOnlyRouter

# 媒体文件想要通过ip地址访问到静态文件要做如下配置

# Routers provide a way of automatically determining the URL conf.
# router = routers.DefaultRouter(trailing_slash=False)
# trailing_slash=False 代表尾部斜杠参数
# router = CustomReadOnlyRouter()
# # 用户注册， 以及用户详情
# router.register(r'users', UserViewSet, base_name='users')
# # 验证码发送
# router.register(r'code', SmsCodeViewset, base_name='code')
# router.register(r'groups', GroupViewSet, base_name='groups',)
# router.register(r'groups', GroupViewSet)
# 用户登陆
# router.register(r'login', obtain_jwt_token, base_name='login')

# Wire up our API using automatic URL routing. 
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="index.html")),
    url(r'', include('apps.users.urls')),
    url(r'', include('apps.electron.urls')),
    url(r'', include('apps.scheme.urls')),
    url(r'', include('apps.config.urls')),
    url(r'', include('apps.product.urls')),
    url(r'', include('apps.order.urls')),
    url(r'', include('apps.carts.urls')),
    url(r'', include('apps.verifications.urls')),
    # url(r'^', include('drf_autodocs.urls')),
    # url(r'^', include('drf_autodocs.urls')) ,
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include_docs_urls(title='IC魔方接口文档', public=False), ),
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

