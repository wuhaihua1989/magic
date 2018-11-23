from django.conf.urls import (include, url)
from .views import views_back,views_front
from rest_framework import routers
from magic.settings import PREFIX, PREFIX_BACK

router = routers.DefaultRouter()
router.register(r'^' + PREFIX_BACK + 'schemes/categories', views_back.SchemeCategoryViewSet)
router.register(r'^' + PREFIX_BACK + 'schemes/scheme', views_back.SchemeViewSet)
# router.register(r'^' + PREFIX_BACK + 'schemes/designs', views.SchemeSystemDesignViewSet)
router.register(r'^' + PREFIX_BACK + 'schemes/electrons', views_back.SchemeElectronViewSet)
router.register(r'^' + PREFIX_BACK + 'schemes/category', views_back. BackSchemeCategoryViewSet)#方案类型
# router.register(r'^' + PREFIX_BACK + 'schemes/update', views_back.SchemeRetrieveUpdateViewSet)#方案详情更新
router.register(r'^' + PREFIX_BACK + 'schemes/ele_delete', views_back.SchemeBomElectronDeleteViewset)#方案元器件删除
router.register(r'^' + PREFIX_BACK + 'schemes/ele_search', views_back.SchemeBomElectronViewset)#方案元器件搜索

# router.register(r'^' + PREFIX_BACK + 'schemes/videos', views.SchemeVideoViewSet)
# router.register(r'^' + PREFIX_BACK + 'schemes/designs', views.SchemeSystemDesignViewSet)
# router.register(r'^' + PREFIX_BACK + 'schemes/images', views.SchemeImageViewSet)
# router.register(r'^' + PREFIX_BACK + 'schemes/code', views.ElectronDataSheetViewSet)
router.register(r'^' + PREFIX_BACK + 'schemes/similar', views_back.SimilarSchemeViewSet)
router.register(r'^' + PREFIX_BACK + 'schemes/detail', views_front.SchemeDetailViewSet) #方案详情
# router.register(r'^' + PREFIX_BACK + 'schemes/search', views_front.SchemeElectronSearch) #方案详情

# router.register(r'ic/schemes/user/new', views_front.NewSchemeViewSet)#
router.register(r'ic/user/schemes', views_front.NewSchemeDetailViewSet) #用户方案详情
router.register(r'ic/schemes/categories', views_front.NewSchemeCategoryViewSet) #方案类型
router.register(r'ic/schemes/electrons', views_front.SchemeBomElectronViewset)#方案元器件搜索
router.register(r'ic/schemes/rf_ele', views_front.SchemeElectronDeleteViewset)#方案元器件删除
# router.register(r'ic/schemes/electron/', views_front.SchemeElectronSearchViewset)#方案元器件删除


# router.register(r'scheme_consumers', views.SchemeConsumerViewSet)
# router.register(r'^' + PREFIX_BACK + 'users/members', UserMemberView)

urlpatterns = [
    url('', include(router.urls)),
    url('^ic/schemes/new/$', views_front.NewSchemeViewSet.as_view()),#个人方案新建，更新
    url('^ic/magic/schemes/update/$', views_back.SchemeRetrieveUpdate.as_view()),#方案新建，更新
    url('^ic/schemes/similar/$', views_front.SchemeSimilarSearch.as_view()),
    url('^ic/schemes/product/$', views_front.SchemeProductSearch.as_view()),
    url('^ic/schemes/electron/$', views_front.SchemeElectronSearch.as_view()),
    url('^ic/schemes/search/$', views_front.IndexSchemeSearch.as_view()),
]
