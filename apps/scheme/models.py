from django.db import models
from apps.electron.models import Electron, ElectronCategory
from apps.users.models import User


# Create your models here.
# 方案类型
class SchemeCategory(models.Model):
    """方案类型"""
    # CATEGORY_TYPE = (
    #     (0, "一级类目"),
    #     (1, "二级类目"),
    #     (2, "三级类目"),

    name = models.CharField(max_length=188, verbose_name='类目描述', unique=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    image = models.CharField(max_length=288, verbose_name='图片', null=True, blank=True)

    class Meta:
        db_table = 'm_scheme_category'
        verbose_name = u"方案类型"
        verbose_name_plural = u'方案类型'

    def __str__(self):
        return self.name


# 方案
class Scheme(models.Model):
    """应用方案"""
    title = models.CharField(max_length=188, verbose_name='方案名称')
    scheme_user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="下单用户", related_name='scheme_user')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格', null=True, blank=True)
    category = models.ForeignKey(SchemeCategory, on_delete=models.CASCADE, verbose_name='方案类型')
    tags = models.CharField(max_length=566,verbose_name='标签', null=True, blank=True)  # ; 根据方案名称分词截

    images = models.CharField(max_length=566, verbose_name='图片', null=True, blank=True)

    source_code = models.CharField(max_length=566,verbose_name='源码', null=True, blank=True)
    code_name = models.CharField(max_length=188, verbose_name='源码名称', null=True, blank=True)
    desc_specific = models.TextField(verbose_name='特性', null=True,blank=True)
    describe = models.TextField(verbose_name='描述', null=True,blank=True)
    is_reference = models.BooleanField(default=False, verbose_name='参考设计')  # 根据字段判断是否需要收费
    views = models.IntegerField(default=0, verbose_name='浏览量', null=True, blank=True)
    source_web = models.CharField(max_length=366, verbose_name='来源站点', null=True, blank=True)  # 如果是用户创建的话，站点是用户名
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='抓取时间')  # 创建时间

    """付费或分享了该方案的用户"""
    consumer = models.ManyToManyField(User, through="SchemeConsumer", related_name='scheme_consumers', verbose_name='方案的消费者')
    download_count = models.IntegerField(default=0, verbose_name='下载次数', null=True, blank=True)

    # 方案视频 SchemeVideo
    # 方案原理图 SchemeSystemdesign
    # Bom清单 SchemeElectron

    # 联系信息
    contact_name = models.CharField(max_length=166, verbose_name='联系人', null=True, blank=True)
    contact_tel = models.CharField(max_length=166, verbose_name='联系电话', null=True, blank=True)
    enterprise = models.CharField(max_length=166, verbose_name='企业名称', null=True, blank=True)
    contact_qq = models.CharField(max_length=166, verbose_name='联系QQ', null=True, blank=True)
    contact_email = models.EmailField(verbose_name='联系邮箱', null=True, blank=True)

    class Meta:
        db_table = 'm_scheme'
        verbose_name = u"方案"
        verbose_name_plural = u'方案'

    def __str__(self):
        return self.title


# 相似方案
class SimilarScheme(models.Model):
    scheme= models.ForeignKey(Scheme, related_name='similars', on_delete=models.CASCADE, verbose_name='元器件')
    similar = models.ForeignKey(Scheme, related_name='similar_schemes', on_delete=models.CASCADE, verbose_name='可替换方案')
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'm_scheme_similar'
        verbose_name = u'可替换元器件'
        verbose_name_plural = u'可替换元器件'


# 方案系统设计图
class SchemeSystemDesign(models.Model):
    """方案原理图"""
    name = models.CharField(max_length=166, verbose_name='名称', help_text='名称')
    image = models.CharField(max_length=566, verbose_name='图片链接')
    download_count = models.IntegerField(default=0, verbose_name='下载量')
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, verbose_name='方案', help_text='方案', related_name='designs')

    class Meta:
        db_table = 'm_scheme_system_design'
        verbose_name = u'方案系统框图'
        verbose_name_plural = u'方案系统框图'

    def __str__(self):
        return self.name


# 方案消费者
class SchemeConsumer(models.Model):
    """参考设计方案付费用户"""
    is_share = models.BooleanField(default=False, verbose_name='分享')
    is_pay = models.BooleanField(default=False, verbose_name='付费')
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, verbose_name='方案')
    consumer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='消费者')

    class Meta:
        db_table = 'm_scheme_consumer'
        verbose_name = u'方案消费者'
        verbose_name_plural = u'方案消费者'


# 方案元器件
class SchemeElectron(models.Model):
    """方案元器件应用 bill of meterial (物料清单) Bom清单"""
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='electrons')
    model_name = models.ForeignKey(Electron, on_delete=models.CASCADE,related_name='sheme_electrons')  # 与元器件表对应
    model_des = models.CharField(max_length=266, verbose_name='描述', null=True, blank=True)
    is_key = models.BooleanField(default=False)   # 是否是关键的元器件部件
    is_record = models.BooleanField(default=False)  # 数据库中是否有该元器件
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'm_scheme_electron'
        verbose_name = u"方案元器件"
        verbose_name_plural = u'方案元器件'

    def __str__(self):
        return self.model_name


# 方案的技术文档
class SchemeDocuments(models.Model):
    """方案技术文档"""
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE,related_name='documents')
    name = models.CharField(max_length=188, null=True, blank=True, verbose_name='文档名称', help_text='文档名称')
    url = models.CharField(max_length=288, verbose_name='文件路径', null=True, blank=True)

    class Meta:
        db_table = 'm_scheme_documents'
        verbose_name = u'方案技术文档'
        verbose_name_plural = u'方案技术文档'

    def __str__(self):
        return self.name


# 方案视频
class SchemeVideo(models.Model):
    """方案视频"""
    
    url = models.CharField(max_length=288, verbose_name='视频地址', null=True, blank=True)
    name = models.CharField(max_length=288, verbose_name='视频名称', null=True, blank=True)
    title = models.CharField(max_length=188, verbose_name='标题')
    is_primary = models.BooleanField(default=False, verbose_name='是否是主视频')  # 主视频不能大于15秒，否则设置失败
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, verbose_name='方案', related_name='videos')
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'm_scheme_video'
        verbose_name = u'方案视频'
        verbose_name_plural = u'方案视频'

    def __str__(self):
        return self.title

