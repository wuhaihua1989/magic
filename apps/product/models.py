from django.db import models
from apps.scheme.models import Scheme
from apps.electron.models import Electron
from apps.users.models import User
from utils.Basemodels import BaseModel


# 成品类别
class ProductCategory(models.Model):
    """成品类型"""
    name = models.CharField(max_length=188, verbose_name='类目描述', unique=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    image = models.CharField(max_length=366, verbose_name='类型图片', null=True, blank=True)

    class Meta:
        db_table = 'm_product_category'
        verbose_name = u"成品类型"
        verbose_name_plural = u'成品类型'

    def __str__(self):
        return self.name


# 产品
class Product(BaseModel):
    """成品"""
    name = models.CharField(max_length=166, verbose_name='名称')
    price = models.FloatField(verbose_name='价格', default=0, null=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name='类型')
    views = models.IntegerField(default=0, verbose_name='浏览量', null=True, blank=True)
    desc = models.TextField(verbose_name='成品描述', null=True, blank=True)
    source_web = models.CharField(max_length=366, verbose_name='来源站点', null=True, blank=True)  # 如果是用户创建的话，站点是用户名
    images = models.TextField(verbose_name='图片地址', null=True, blank=True)
    origin = models.CharField(max_length=16, verbose_name='产地', null=True, blank=True)
    market_date_at = models.DateTimeField(verbose_name='上市时间', null=True, blank=True)
    factory = models.CharField(max_length=366, verbose_name='生产商', null=True, blank=True)
    scheme = models.ManyToManyField(Scheme, verbose_name='成品方案', related_name='products')

    class Meta:
        db_table = 'm_product'
        verbose_name = u"成品"
        verbose_name_plural = u'成品'

    def __str__(self):
        return self.name + "-" + self.category.name


# 成品视频
class ProductVideo(BaseModel):
    """成品视频"""
    url = models.TextField(verbose_name='视频地址', null=True, blank=True)
    name = models.CharField(max_length=188, verbose_name='视频名称', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='成品', related_name='videos')
    is_key = models.BooleanField(default=False, verbose_name='是否主视图')

    class Meta:
        db_table = 'm_product_video'
        verbose_name = u'成品视频'
        verbose_name_plural = u'成品视频'


# 产品的Bom清单
class ProductElectron(BaseModel):
    """成品的Bom清单"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='成品', related_name='electrons')
    model_name = models.ForeignKey(Electron, on_delete=models.CASCADE, related_name='pro_electrons')
    model_desc = models.CharField(max_length=366, verbose_name='描述', null=True, blank=True)
    is_key = models.BooleanField(default=False, verbose_name='是否是主要器件')

    class Meta:
        db_table = 'm_product_electron'
        verbose_name = u'成品BOM清单'
        verbose_name_plural = u'成品BOM清单'

    def __str__(self):
        return self.product.name + "-" + self.model_name.model_name


# 个性化配置成品
class CustomProduct(BaseModel):
    """个性化配置成品（基于某一款成品）"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='成品')
    # 个性化定制联系人用户
    consumer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')

    # 个性化元器件配置 存储在 CustomProductScheme 中（对应多条数据）
    # 个性化方案配置  存储在  CustomProductElectron 中（对应多条数据）
    # 外观和厂商要求 
    appearance = models.CharField(max_length=266, verbose_name='外观', null=True, blank=True)
    factory = models.CharField(max_length=166, verbose_name='生产加工', null=True, blank=True)

    class Meta:
        db_table = 'm_custom_product'
        verbose_name = u'个性化定制成品'
        verbose_name_plural = u'个性化定制成品'

    def __str__(self):
        return self.product.name


# 个性化配置成品的方案
class CustomProductScheme(BaseModel):
    """个性化配置方案"""
    custom_product = models.ForeignKey(CustomProduct, on_delete=models.CASCADE, verbose_name='个性化配置成品', related_name='schemes_custom')
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, verbose_name='方案', null=True, blank=True, related_name='custom_scheme')  # 已收录填入
    scheme_name = models.CharField(max_length=366, verbose_name='方案名称', null=True, blank=True)  # 未收录填入
    is_record = models.BooleanField(default=False, verbose_name='是否收录')  # 数据库中是否存在

    class Meta:
        db_table = 'm_custom_product_scheme'
        verbose_name = u"个性化成品方案"
        verbose_name_plural = u'个性化成品方案'

    def __str__(self):
        return self.scheme.title


# 个性化配置成品的元器件
class CustomProductElectron(BaseModel):
    """个性化配置元器件"""
    custom_product = models.ForeignKey(CustomProduct, on_delete=models.CASCADE, verbose_name='个性化配置元器件', related_name='electrons_custom')
    electron = models.ForeignKey(Electron, on_delete=models.CASCADE, verbose_name='元器件', null=True, blank=True, related_name='custom_electrons')
    model_name = models.CharField(max_length=366, verbose_name='模型名称', null=True, blank=True)
    is_record = models.BooleanField(default=False, verbose_name='是否收录')  # 收录过的数据会存储electron，未收录存储型号字段
    is_key = models.BooleanField(default=False, verbose_name='是否是主要器件')

    class Meta:
        db_table = 'm_custom_product_electron'
        verbose_name = u"个性化成品器件"
        verbose_name_plural = u'个性化成品器件'

    def __str__(self):
        return self.custom_product.product.name
