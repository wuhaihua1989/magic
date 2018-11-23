from django.db import models

from utils.Basemodels import BaseModel
# Create your models here.


class WebSite(BaseModel):
    """
    网站信息
    """
    company = models.CharField(max_length=188, verbose_name='公司名称', null=True, blank=True)
    industry = models.CharField(max_length=188, verbose_name='行业类别', null=True, blank=True)
    tel_man = models.CharField(max_length=188, verbose_name='联系人', null=True, blank=True)
    mail_code = models.CharField(max_length=166, verbose_name='邮编', null=True, blank=True)
    four_tel_number = models.CharField(max_length=166, verbose_name='400电话', null=True, blank=True)
    fax = models.CharField(max_length=166, verbose_name='传真', null=True, blank=True)
    email = models.EmailField(max_length=166, verbose_name='邮箱', null=True, blank=True)
    tel_number = models.CharField(max_length=166, verbose_name='座机', null=True, blank=True)
    qq = models.CharField(max_length=166, verbose_name='客服QQ', null=True, blank=True)
    address = models.CharField(max_length=266, verbose_name='联系地址', null=True, blank=True)
    web_site = models.CharField(max_length=188, verbose_name='公司网站', null=True, blank=True)
    logo = models.TextField(verbose_name='logo', null=True, blank=True)
    source = models.TextField(verbose_name='图片', null=True, blank=True)
    description = models.TextField(verbose_name='公司描述', null=True, blank=True)

    class Meta:
        db_table = 'm_website'
        verbose_name = u'网站'
        verbose_name_plural = u'网站'


# SEO
class SEO(BaseModel):
    """
    SEO 信息
    """
    title = models.CharField(max_length=266, verbose_name='标题', null=True, blank=True)
    key = models.CharField(max_length=266, verbose_name='关键字', null=True, blank=True)
    description = models.TextField(verbose_name='描述', null=True, blank=True)

    class Meta:
        db_table = 'm_seo'
        verbose_name = u'SEO信息'
        verbose_name_plural = u'SEO信息'


# 网站协议
class Protocol(BaseModel):
    context = models.TextField(verbose_name='协议内容', null=True, blank=True)

    class Meta:
        db_table = 'm_protocol'
        verbose_name = u'网站协议'
        verbose_name_plural = u'网站协议'


# 内容分类
class MagicContentCategory(models.Model):
    """
    内容类型
    """
    level = models.CharField(max_length=166, verbose_name='内容分类')

    icon = models.CharField(max_length=512, verbose_name='图片', null=True, blank=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        db_table = 'm_magic_content_category'
        verbose_name = u'内容类型'
        verbose_name_plural = u'内容类型'

    def __str__(self):
        return self.level


# 添加 内容
class MagicContent(BaseModel):
    """
    内容
    """
    title = models.CharField(max_length=266, verbose_name='标题', null=True, blank=True)
    category = models.ForeignKey(MagicContentCategory, on_delete=models.CASCADE, verbose_name='类型')
    content = models.TextField(verbose_name='填充内容', null=True, blank=True)
    enable = models.BooleanField(default=False, verbose_name='是否启用')

    class Meta:
        db_table = 'm_magic_content'
        verbose_name = u'内容'
        verbose_name_plural = u'内容'


# 物流计价规格表
class FreightCarrier(models.Model):
    max_money = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='最大金额') # 大于等于此金额将免运费
    is_gd = models.BooleanField(default=False, verbose_name='是否是广东地区')
    gd_freight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='同城费用')
    another_freight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='异地费用')

    class Meta:
        db_table = 'm_freight_carrier'
        verbose_name = '运费计价规则'
        verbose_name_plural = '运费计价规则'


class Image(models.Model):
    image = models.ImageField(upload_to="images", verbose_name='image_set', null=True, blank=True)

    class Meta:
        db_table = 'm_db_img'
        verbose_name = u'图集'
        verbose_name_plural = verbose_name


class Video(models.Model):
    videos = models.FileField(upload_to="videos", verbose_name='video_set', null=True, blank=True)

    class Meta:
        db_table = 'm_db_videos'
        verbose_name = u'视频集'
        verbose_name_plural = verbose_name


class Files(models.Model):
    files = models.FileField(upload_to="files", verbose_name='files_set',null=True, blank=True)

    class Meta:
        db_table = 'm_db_files'
        verbose_name = u'文件集'
        verbose_name_plural = verbose_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        print(force_insert)
        print(force_update)
        print(using)
        print(update_fields)

        return super().save()


class LeaveMessage(BaseModel):
    name = models.CharField(max_length=88, verbose_name=u'留言人姓名')
    email = models.EmailField(max_length=188, verbose_name=u'留言人email')
    content = models.TextField(verbose_name=u'留言内容')

    class Meta:
        db_table = 'm_leave_message'
        verbose_name = u'建议或意见留言'
        verbose_name_plural = verbose_name







