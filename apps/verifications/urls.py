from django.conf.urls import url
from . import views
urlpatterns = [
    # url(r'image_code/(?P<image_code_id>.+)/$', views.ImageCodeView.as_view()),
    url(r'ic/image_code/(?P<image_code_id>.+)/$', views.ImageCodeView.as_view()),
    url(r'ic/sms_code/$', views.SMSCodeView.as_view()),
    url(r'ic/sms_code/token/$', views.SMSCodeByTokenView.as_view()),

]