from rest_framework import serializers
from django_redis import get_redis_connection
from redis import RedisError
from apps.users.models import User
import logging
import re
from magic.settings import REGEX_MOBILE
logger = logging.getLogger('magic')

class ImageCodeCheckSerializer(serializers.Serializer):
    """检查图片验证码的序列化器"""
    image_code_id = serializers.UUIDField()
    image_code = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):

        image_code_id = attrs["image_code_id"]
        print(image_code_id)
        image_code = attrs["image_code"]
        redis_conn = get_redis_connection("verify_codes")
        # 从redis中获取真实的图片验证码
        real_image_code_text = redis_conn.get('img_%s'%image_code_id)
        print(real_image_code_text)
        # 如果图片验证码过期或者没有
        if not real_image_code_text:
            raise serializers.ValidationError('图片验证码无效')
        try:
            # 删除一个不存在的键，会报错
            redis_conn.delete('img_%s'% image_code_id)
        except RedisError as e:
            logger.error(e)
        # 因为直接从redis中获取到的数据是bytes类型，需要转码
        real_image_code_text = real_image_code_text.decode()
        if real_image_code_text.lower() != image_code.lower():
            raise serializers.ValidationError('图片验证码错误')

        # 检查是否在60s内有发送记录
        mobile = self.context['view'].kwargs.get("mobile")
        if mobile:
            send_flag = redis_conn.get("send_flag_%s" % mobile)

            if send_flag:
                raise serializers.ValidationError('请求次数过于频繁')
        return attrs

class CheckAccessTokenForSMSSerializer(serializers.Serializer):

    access_token = serializers.CharField(label='发送短信的临时票据access_token', required=True, allow_null=False)

    def validate(self,attrs):
        # 获取发送短信的凭证 access_token，并校验
        access_token = attrs["access_token"]

        # 从user.User模型中调用验证access_token的方法
        mobile = User.check_sms_code_token(access_token)
        if not mobile:
            raise serializers.ValidationError("无效或错误的access_token")

        # 判断60s内是否发送过短信
        redis_conn = get_redis_connection("verify_codes")
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        if send_flag:
            raise serializers.ValidationError('请求次数过于频繁')

        self.mobile = mobile

        return attrs



class SmsSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11, required=True, label="手机号码")

    def validate_mobile(self, mobile):
        """
        验证手机号码
        :param data:
        :return:
        """

        # 手机是否注册
        if User.objects.filter(mobile=mobile).count():
            raise serializers.ValidationError("手机号码已经存在")

        # 验证手机号码是否合法
        if not re.match(REGEX_MOBILE, mobile):
            raise serializers.ValidationError("手机号码非法")

        return mobile