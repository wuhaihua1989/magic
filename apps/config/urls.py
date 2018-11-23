from django.conf.urls import (include, url)
from .views import *
from rest_framework import routers
from magic.settings import PREFIX, PREFIX_BACK

# freight_list = FreightViewSet.as_view({'get': 'list', 'post': 'create'})
# freight_create = FreightViewSet.as_view({'post': 'create'})

router = routers.DefaultRouter()
router.register(PREFIX_BACK + r'config/freights', FreightViewSet)
router.register(PREFIX_BACK + r'config/websites', WebSetViewSet)
router.register(PREFIX_BACK + r'config/content_categories', ContentCategoryViewSet)
router.register(PREFIX_BACK + 'config/seo', SEOViewSet)
router.register(PREFIX_BACK + 'config/protocol', ProtocolViewSet)
router.register(PREFIX_BACK + r'config/magic_content', MagicContentViewSet)
router.register(PREFIX_BACK + r'config/hot_model', HotModelViewSet)
router.register(r'ic/image_url', ImageStorageViewSet)
router.register(r'ic/video_url', VideoStorageViewSet)
router.register(r'ic/file_url', FileStorageViewSet)
router.register(PREFIX_BACK + r'leave/message', LeaveMessageViewSet)

urlpatterns = [
    # url(r'^freights/list/$', freight_list, name='freight-list'),
    url(r'', include(router.urls)),
    url(r'^ic/searches/$', SaveSearchCount.as_view()),
    url(r'^ic/base/info/$', GetSearchCount.as_view()),
    url(r'^ic/hot/all/$', AllHotElectronSchemeProduct.as_view()),
]
