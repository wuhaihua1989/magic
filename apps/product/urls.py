from rest_framework import routers
from django.conf.urls import url, include

from magic.settings import PREFIX, PREFIX_BACK
from .views.views_back import ProductCategoryViewSet, ProductViewSet, CustomProductViewSet
from .views.views_front import ProductDetailHomeViewSet, CustomProductDetailHomeViewSet, CustomProductHomeViewSet
from .views.views_front import CustomProductUserViewSet, CommentViewSet, IndexProductRecommendViewSet
from .views.views_front import IndexElectronRecommendViewSet, IndexSchemeRecommendViewSet
from .views.views_back import ProductElectronSearchViewSet, ProductSchemeSearchViewSet


router = routers.DefaultRouter()
"""后台url"""
# 成品分类
router.register(PREFIX_BACK + 'products/categories', ProductCategoryViewSet, base_name="products_categories")
# 成品
router.register(PREFIX_BACK + 'products/product', ProductViewSet, base_name="products")
# 成品方案搜索
router.register(PREFIX_BACK + 'products/scheme/search', ProductSchemeSearchViewSet, base_name="scheme_search")
# 成品BOM元器件搜索
router.register(PREFIX_BACK + 'products/electron/search', ProductElectronSearchViewSet, base_name="electron_search")
# 成品定制
router.register(PREFIX_BACK + 'products/customs', CustomProductViewSet, base_name="customs")

"""前台url"""
# 成品详情
router.register(PREFIX + 'products/detail', ProductDetailHomeViewSet, base_name="products_detail")
# 个性化定制详情
router.register(PREFIX + 'products/customs/detail', CustomProductDetailHomeViewSet, base_name="customs_detail")
# 个性化定制提交
router.register(PREFIX + 'products/customs', CustomProductHomeViewSet, base_name="products_customs")
# 提交个性化定制时用户完善
router.register(PREFIX + 'products/customs/user', CustomProductUserViewSet, base_name="customs_user")
# 用户评论
router.register(PREFIX + 'comment', CommentViewSet, base_name="comment")
# 首页智能推荐:推荐成品
router.register(PREFIX + 'index/product', IndexProductRecommendViewSet, base_name="recommend_product")
# 首页智能推荐:推荐元器件
router.register(PREFIX + 'index/electron', IndexElectronRecommendViewSet, base_name="recommend_electron")
# 首页智能推荐:推荐方案
router.register(PREFIX + 'index/scheme', IndexSchemeRecommendViewSet, base_name="recommend_scheme")

urlpatterns = [
    url('', include(router.urls)),
]
