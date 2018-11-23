from django.conf.urls import url

from magic.settings import PREFIX_BACK
from apps.carts import views

urlpatterns = [
    url(r'^'+PREFIX_BACK+'carts/$', views.CartView.as_view()),
]