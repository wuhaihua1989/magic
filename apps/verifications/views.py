from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from django_redis import get_redis_connection
from django.http.response import HttpResponse
from rest_framework.response import Response
from rest_framework import status
import random
from django_redis import get_redis_connection
from . import constants
from . import serializers
from libs.yuntongxun.sms import CCP
from libs.captcha.captcha import captcha
from apps.users.models import User
from rest_framework import status, mixins, viewsets
from .serializers import SmsSerializer


class ImageCodeView(APIView):
    """图片验证码"""
    def get(self,request,image_code_id):

        image_code_id = image_code_id.lower()
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection("verify_codes")

        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES,text)

        return HttpResponse(image, content_type="images/jpg")


class SMSCodeView(GenericAPIView):
    """短信验证码"""

    serializer_class = serializers.ImageCodeCheckSerializer
    def get(self,request,*args, **kwargs):
        # 在序列化器中 检查图片验证码和检查是否在60s内有发送记录
        print(request.query_params)
        mobile =request.query_params['mobile']
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        redis_conn = get_redis_connection('verify_codes')
        # 生成短信验证码
        sms_code = "%06d" % random.randint(0,999999)
        #保存短信验证码与发送记录
        print(sms_code)
        pl = redis_conn.pipeline()
        pl.multi()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 发送短信的标志，维护60秒
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        # 发送短信
        ccp = CCP()
        time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
        try:
            ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_TEMP_ID)
        except Exception as e:
            print(e)
        # 调用celery异步发送短信
        # send_sms_code.delay(mobile,sms_code)
        return Response({"message": "短信已发送"}, status.HTTP_200_OK)


class SMSCodeByTokenView(GenericAPIView):
    serializer_class = serializers.CheckAccessTokenForSMSSerializer
    """凭借access_token发送短信验证码"""
    def get(self,request):
        # 获取序列化器对象
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 生成短信验证码
        sms_code = "%06d" % random.randint(0,999999)

        # 从序列化器对象中提取手机号
        mobile = serializer.mobile
        print(mobile)

        # 保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')

        pl = redis_conn.pipeline()
        pl.multi()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 发送短信的标志，维护60秒
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute() # 把上面组装的操作一并执行
        # 用celery异步发送短信，异步任务函数中的参数，必须一一按照顺序填写到delay中
        # send_sms_code.delay(mobile,sms_code
        ccp = CCP()
        time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
        try:
            ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_TEMP_ID)
        except Exception as e:
            print(e)


        return Response({"message": "OK"}, status.HTTP_200_OK)


class SmsCodeViewset(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    发送短信验证码
    """
    serializer_class = SmsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile = serializer.validated_data["mobile"]
        redis_conn = get_redis_connection('verify_codes')

        send_flag = redis_conn.get("send_flag_%s" % mobile)

        if send_flag:
            return Response({"message": "请求频繁"})

        # 生成短信验证码
        sms_code = "%06d" % random.randint(0, 999999)
        # 保存短信验证码与发送记录
        print(sms_code)
        pl = redis_conn.pipeline()
        pl.multi()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 发送短信的标志，维护60秒
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        # 发送短信
        ccp = CCP()
        time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
        try:
            ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_TEMP_ID)
        except Exception as e:
            print(e)
            return Response({"error": e})

        return Response({"message": "短信已发送"}, status=status.HTTP_201_CREATED)
