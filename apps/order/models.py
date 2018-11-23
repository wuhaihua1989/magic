from django.db import models
from apps.electron.models import Electron, ElectronVideo, Supplier
from apps.users.models import User, Address
from apps.scheme.models import Scheme
from utils.Basemodels import BaseModel


# Create your models here.
class OrderInfo(BaseModel):
    """
    订单信息
    """
    PAY_METHODS_ENUM = {  # 支付方式，作为程序的判断条件，执行不同的下单流程

        "ALIPAY": 1,
        "WEXIN": 2

    }

    PAY_METHOD_CHOICES = (  # 给用户看
        (1, "支付宝"),
        (2, "微信"),
    )

    ORDER_STATUS_ENUM = {
        "UNPAID": 1,
        "UNSEND": 2,
        "UNRECEIVED": 3,
        "FINISHED": 4,
        "CLOSED": 5,
        "RETURNED":6
    }

    ORDER_STATUS_CHOICES = (
        (1, "待支付"),
        (2, "待发货"),
        (3, "待收货"),
        (4, "已完成"),
        (5, "已取消"),
        (6, "已退款"),
    )
    RECEIPT_TPYE_ENUM = {
        "NONEED": 1,
        "PERSON": 2,
        "COMPANY": 3,

    }

    RECEIPT_TPYE_CHOICES = (
        (1, "不须发票"),
        (2, "个人"),
        (3, "企业"),

    )

    order_id = models.CharField(max_length=64, primary_key=True, verbose_name="订单号")
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="下单用户", related_name='user')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, verbose_name="收货地址")
    total_count = models.IntegerField(default=1, verbose_name="商品总数")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="商品总金额")
    freight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="运费")
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=1, verbose_name="支付方式")
    status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=2, verbose_name="订单状态", )
    Courier_company = models.CharField(max_length=32, verbose_name="快递公司", null=True, blank=True)
    Courier_no = models.CharField(max_length=64, verbose_name="快递单号", null=True, blank=True)
    Courier_time = models.DateTimeField(verbose_name="发货时间",null=True, blank=True)

    receive_goods = models.BooleanField(default=False, verbose_name='是否收货')
    receipt = models.SmallIntegerField(choices=RECEIPT_TPYE_CHOICES, default=1, verbose_name="发票类型")
    rel_name = models.CharField(max_length=188, verbose_name='个人发票抬头', null=True, blank=True)
    company_name = models.CharField(max_length=188, verbose_name='公司名称', help_text='公司名称', null=True, blank=True)
    company_tax_number = models.CharField(max_length=188, verbose_name='纳税识别号', help_text='电话号码', null=True, blank=True)

    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,verbose_name='退款金额')
    describe = models.TextField(verbose_name='退款描述', null=True, blank=True)
    class Meta:
        db_table = "m_order_info"
        verbose_name = '订单基本信息'
        verbose_name_plural = verbose_name


# 订单元对应器件
class OrderElectron(models.Model):
    """
    订单对应的元器件数量，价格，
    """
    order = models.ForeignKey(OrderInfo, related_name='eles', on_delete=models.CASCADE, verbose_name="订单")
    eles = models.ForeignKey(Electron, on_delete=models.PROTECT, verbose_name="订单商品")
    count = models.IntegerField(default=1, verbose_name="数量")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")

    class Meta:
        db_table = 'm_order_electron'
        verbose_name = u'订单元器件'
        verbose_name_plural = u'订单元器件'


# class InvoiceInfo(BaseModel):
#
#     user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="用户")
#     order = models.ForeignKey(OrderInfo, related_name='eles', on_delete=models.CASCADE, verbose_name="订单")
#     invoice_title = models.CharField(max_length=188, verbose_name='发票抬头', null=True, blank=True)
#
#     tax_no= models.CharField(max_length=188, verbose_name='公司名称', null=True, blank=True)
#     company_add= models.CharField(max_length=188, verbose_name='公司注册地址', null=True, blank=True)
#     tax_number = models.CharField(max_length=188, verbose_name='纳税人识别号', null=True,blank=True)
#     tax_number = models.CharField(max_length=188, verbose_name='纳税人识别号', null=True,blank=True)
#
#     order_address = models.ForeignKey(Address, on_delete=models.PROTECT, verbose_name='收货人', null=True)

class WechatPayment(BaseModel):
    order = models.ForeignKey(OrderInfo, related_name='we_order', on_delete=models.CASCADE, verbose_name="订单")
    pay_no = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='微信支付订单号')
    create_at = models.DateField(auto_now_add=True, verbose_name="创建时间")

class AliPayment(BaseModel):
    order = models.ForeignKey(OrderInfo, related_name='ali_order', on_delete=models.CASCADE, verbose_name="订单")
    pay_no = models.CharField(max_length=64, blank=True, null=True, unique=True, verbose_name='微信支付订单号')
    create_at = models.DateField(auto_now_add=True, verbose_name="创建时间")