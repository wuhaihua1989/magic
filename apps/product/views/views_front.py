from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_redis import get_redis_connection
import redis
from itertools import chain
from django.db.models import Q

from utils.permission import IsOwnerOrReadOnly
from ..pagination import Pagination

from apps.electron.models import Electron, SimilarElectron, PinToPin
from apps.electron.models import UniversalComment
from apps.scheme.models import Scheme, SimilarScheme
from apps.users.models import User
from ..models import Product, ProductElectron, CustomProduct, CustomProductElectron, CustomProductScheme

from ..serializer.serializer_front import ProductDescHomeSerializers, ProductSchemeHomeSerializers
from ..serializer.serializer_front import SimilarProductHomeSerializer, ProductElectronHomeDetailSerializers
from ..serializer.serializer_front import ProductDetailHomeSerializers, CustomProductElectronSelectSerializers
from ..serializer.serializer_front import CustomProductSchemeSelectSerializers, CustomProductHomeRetrieveSerializer
from ..serializer.serializer_front import CustomProductHomeCreateSerializer, CustomProductUserSerializer
from ..serializer.serializer_front import CommentListSerializer, CommentCreateSerializer
from ..serializer.serializer_front import IndexProductRecommendSerializers, IndexElectronRecommendSerializers
from ..serializer.serializer_front import IndexSchemeRecommendSerializers


# ----------------用户界面逻辑----------------


class IndexProductRecommendViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list:首页智能推荐:成品推荐
    """
    serializer_class = IndexProductRecommendSerializers

    def get_queryset(self):
        if not self.request.user.username:
            # 用户未登录时返回的数据
            queryset = Product.objects.all().order_by("-views")[:8]
        else:
            # 用户登录时返回的数据
            username = self.request.user.username
            redis_conn = get_redis_connection("browsing_history")
            product_category_id = redis_conn.get("%s_recommend_product_category_id" % username)
            if product_category_id:
                queryset = Product.objects.filter(category_id=int(product_category_id))
                if queryset.count() >= 8:
                    queryset = queryset.order_by("-views")[:8]
                else:
                    count = queryset.count()
                    queryset1 = Product.objects.filter(~Q(category_id=int(product_category_id))).order_by("-views")[:(8 - count)]
                    queryset = chain(queryset, queryset1)
            else:
                queryset = Product.objects.all().order_by("-views")[:8]

        return queryset


class IndexElectronRecommendViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
        """
        list:首页智能推荐:元器件推荐
        """
        serializer_class = IndexElectronRecommendSerializers

        def get_queryset(self):
            if not self.request.user.username:
                # 用户未登录时返回的数据
                queryset = Electron.objects.filter(isDelete=False).order_by("-views")[:8]
            else:
                # 用户登录时返回的数据
                username = self.request.user.username
                redis_conn = get_redis_connection("browsing_history")
                electron_category_id = redis_conn.get("%s_recommend_electron_category_id" % username)
                if electron_category_id:
                    queryset = Electron.objects.filter(category_id=int(electron_category_id), isDelete=False)
                    if queryset.count() >= 8:
                        queryset = queryset.order_by("-views")[:8]
                    else:
                        count = queryset.count()
                        queryset1 = Electron.objects.filter(~Q(category_id=int(electron_category_id)), isDelete=False).order_by("-views")[:(8 - count)]
                        queryset = chain(queryset, queryset1)
                else:
                    queryset = Electron.objects.filter(isDelete=False).order_by("-views")[:8]

            return queryset


class IndexSchemeRecommendViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    list:首页智能推荐:方案推荐
    """
    serializer_class = IndexSchemeRecommendSerializers

    def get_queryset(self):
        if not self.request.user.username:
            # 用户未登录时返回的数据
            queryset = Scheme.objects.all().order_by("-views")[:8]
        else:
            # 用户登录时返回的数据
            username = self.request.user.username
            redis_conn = get_redis_connection("browsing_history")
            scheme_category_id = redis_conn.get("%s_recommend_scheme_category_id" % username)
            if scheme_category_id:
                queryset = Scheme.objects.filter(category_id=int(scheme_category_id))
                if queryset.count() >= 8:
                    queryset = queryset.order_by("-views")[:8]
                else:
                    count = queryset.count()
                    queryset1 = Scheme.objects.filter(~Q(category_id=int(scheme_category_id))).order_by("-views")[:(8 - count)]
                    queryset = chain(queryset, queryset1)
            else:
                queryset = Scheme.objects.all().order_by("-views")[:8]

        return queryset


class ProductDetailHomeViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    retrieve：成品详情
    pdesc:成品介绍
    pscheme:方案拆解
    pproduct:同类成品推荐
    pelectron:核心器件
    """
    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.action == "pdesc":
            return ProductDescHomeSerializers
        elif self.action == "pscheme":
            return ProductSchemeHomeSerializers
        elif self.action == "pproduct":
            return SimilarProductHomeSerializer
        elif self.action == "pelectron":
            return ProductElectronHomeDetailSerializers
        else:
            return ProductDetailHomeSerializers

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save()
        serializer = self.get_serializer(instance)

        # 如果用户登录, 保存用户最后浏览的成品类型ID
        if self.request.user.username:

            username = self.request.user.username
            conn = redis.Redis(host="127.0.0.1", port=6379, db=6)
            product = Product.objects.get(id=int(kwargs['pk']))
            product_category_id = product.category_id
            category_id = conn.get("%s_recommend_product_category_id" % username)
            if not category_id or int(category_id) != product_category_id:
                conn.set("%s_recommend_product_category_id" % username, product_category_id, ex=None)

        return Response(serializer.data)

    @action(['get'], detail=True)
    def pdesc(self, request, *args, **kwargs):
        try:
            queryset = Product.objects.filter(id=int(kwargs["pk"]))
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})

    @action(['get'], detail=True)
    def pscheme(self, request, *args, **kwargs):
        """方案拆解"""
        try:
            queryset = Product.objects.filter(id=int(kwargs["pk"]))
            serializer = self.get_serializer(queryset, many=True)
            scheme_list = serializer.data[0]["scheme"]
            sorted_list = sorted(scheme_list, key=lambda x: x["views"], reverse=True)
            serializer.data[0]["scheme"] = sorted_list
            return Response(serializer.data[0], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})

    @action(['get'], detail=True)
    def pproduct(self, request, *args, **kwargs):
        """同类成品推荐"""
        try:
            product = Product.objects.filter(id=int(kwargs["pk"]))
            queryset = Product.objects.filter(category_id=int(product[0].category_id))
            serializer = self.get_serializer(queryset, many=True)
            data = [produc for produc in serializer.data if produc["id"] != int(kwargs["pk"])]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})

    @action(['get'], detail=True)
    def pelectron(self, request, *args, **kwargs):
        """核心器件(BOM清单)"""
        try:
            product_electrons = ProductElectron.objects.filter(product_id=int(kwargs["pk"]), model_name__isDelete=0)
            queryset = []
            for product_electron in product_electrons:
                pin_to_pin_electrons = PinToPin.objects.filter(
                    electron_id=int(product_electron.model_name_id),
                    electron__isDelete=0,
                    pin_to_pin__isDelete=0
                )
                similar_electrons = SimilarElectron.objects.filter(
                    electron_id=int(product_electron.model_name_id),
                    electron__isDelete=0,
                    similar__isDelete=0
                )
                all_pin_to_pin_set = {x.pin_to_pin_id for x in pin_to_pin_electrons}
                all_similar_electron_set = {y.similar_id for y in similar_electrons}
                count = len(all_pin_to_pin_set | all_similar_electron_set)
                similar_electrons_dict = {
                    'id': product_electron.model_name.id,
                    "model_name": product_electron.model_name.model_name,
                    "desc": product_electron.model_name.desc_specific,
                    "is_key": product_electron.is_key,
                    "count": count
                }
                queryset.append(similar_electrons_dict)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})


class CustomProductDetailHomeViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    用户界面:个性化定制
    retrieve:
            个性化定制详情
    csscheme:
            个性化定制方案选择列表
    cselectron:
              个性化定制元器件选择列表
    """

    queryset = Product.objects.all()

    def get_serializer_class(self):
        if self.action == "cselectron":
            return CustomProductElectronSelectSerializers
        elif self.action == "csscheme":
            return CustomProductSchemeSelectSerializers
        else:
            return CustomProductHomeRetrieveSerializer

    def retrieve(self, request, *args, **kwargs):
        """用户界面:个性化定制-成品元器件和方案列表"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            data = serializer.data
            all_scheme = data["scheme"]
            all_electron = data["electrons"]

            # 重构数据，获取可替代方案数据并返回
            if all_scheme:
                scheme_list = []
                for scheme in all_scheme:
                    all_similar_scheme = SimilarScheme.objects.filter(scheme_id=int(scheme["id"]))
                    single_similar_scheme_list = []
                    if all_similar_scheme:
                        for single_similar_scheme in all_similar_scheme:
                            single_similar_scheme = {
                                "id": single_similar_scheme.similar.id,
                                "title": single_similar_scheme.similar.title
                            }
                            single_similar_scheme_list.append(single_similar_scheme)
                    scheme["similar_schemes"] = single_similar_scheme_list
                    scheme_list.append(scheme)
                data["scheme"] = scheme_list

            # 重构数据，获取可替代元器件数据并返回
            if all_electron:
                electron_list = []
                for electron in all_electron:
                    del_electron = Electron.objects.get(id=int(electron["model_name"]["id"]))
                    if del_electron.isDelete == 1:
                        continue
                    single_similar_electron_list = []
                    all_pin_to_pin = PinToPin.objects.filter(
                        electron_id=int(electron["model_name"]['id']),
                        electron__isDelete=0
                    )
                    if all_pin_to_pin:
                        for single_pin_to_pin in all_pin_to_pin:
                            if single_pin_to_pin.pin_to_pin.isDelete == 1:
                                continue
                            pin_to_pin_electron = {
                                "id": single_pin_to_pin.pin_to_pin.id,
                                "model_name": single_pin_to_pin.pin_to_pin.model_name
                            }
                            single_similar_electron_list.append(pin_to_pin_electron)

                    all_similar_electron = SimilarElectron.objects.filter(
                        electron_id=int(electron["model_name"]['id']),
                        electron__isDelete=0
                    )
                    if all_similar_electron:
                        all_pin_to_pin_set = {x.pin_to_pin_id for x in all_pin_to_pin}
                        all_similar_electron_set = {y.similar_id for y in all_similar_electron}
                        repeat_electron = all_pin_to_pin_set & all_similar_electron_set
                        for single_similar_electron in all_similar_electron:
                            if single_similar_electron.similar.id not in repeat_electron:
                                if single_similar_electron.similar.isDelete == 1:
                                    continue
                                single_electron = {
                                    "id": single_similar_electron.similar.id,
                                    "model_name": single_similar_electron.similar.model_name
                                }
                                single_similar_electron_list.append(single_electron)
                    electron["similar_electrons"] = single_similar_electron_list
                    electron_list.append(electron)
                data["electrons"] = electron_list
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})

    @action(['get'], detail=True)
    def cselectron(self, request, *args, **kwargs):
        """个性化定制元器件选择列表"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            data = serializer.data
            all_electron = data["electrons"]

            # 重构数据，获取可替代元器件数据并返回
            if all_electron:
                electron_list = []
                for electron in all_electron:
                    del_electron = Electron.objects.get(id=int(electron["model_name"]["id"]))
                    if del_electron.isDelete == 1:
                        continue
                    single_similar_electron_list = []
                    all_pin_to_pin = PinToPin.objects.filter(
                        electron_id=int(electron["model_name"]['id']),
                        electron__isDelete=0
                    )
                    if all_pin_to_pin:
                        for single_pin_to_pin in all_pin_to_pin:
                            if single_pin_to_pin.pin_to_pin.isDelete == 1:
                                continue
                            pin_to_pin_electron = {
                                "id": single_pin_to_pin.pin_to_pin.id,
                                "model_name": single_pin_to_pin.pin_to_pin.model_name
                            }
                            single_similar_electron_list.append(pin_to_pin_electron)

                    all_similar_electron = SimilarElectron.objects.filter(
                        electron_id=int(electron["model_name"]['id']),
                        electron__isDelete=0
                    )
                    if all_similar_electron:
                        all_pin_to_pin_set = {x.pin_to_pin_id for x in all_pin_to_pin}
                        all_similar_electron_set = {y.similar_id for y in all_similar_electron}
                        repeat_electron = all_pin_to_pin_set & all_similar_electron_set
                        for single_similar_electron in all_similar_electron:
                            if single_similar_electron.similar.id not in repeat_electron:
                                if single_similar_electron.similar.isDelete == 1:
                                    continue
                                single_electron = {
                                    "id": single_similar_electron.similar.id,
                                    "model_name": single_similar_electron.similar.model_name
                                }
                                single_similar_electron_list.append(single_electron)
                    electron["similar_electrons"] = single_similar_electron_list
                    electron_list.append(electron)
                data["electrons"] = electron_list
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})

    @action(['get'], detail=True)
    def csscheme(self, request, *args, **kwargs):
        """个性化定制方案选择列表"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            data = serializer.data
            all_scheme = data["scheme"]

            # 重构数据，获取可替代方案数据并返回
            if all_scheme:
                scheme_list = []
                for scheme in all_scheme:
                    all_similar_scheme = SimilarScheme.objects.filter(scheme_id=int(scheme["id"]))
                    single_similar_scheme_list = []
                    if all_similar_scheme:
                        for single_similar_scheme in all_similar_scheme:
                            single_similar_scheme = {
                                "id": single_similar_scheme.similar.id,
                                "title": single_similar_scheme.similar.title
                            }
                            single_similar_scheme_list.append(single_similar_scheme)
                    scheme["similar_schemes"] = single_similar_scheme_list
                    scheme_list.append(scheme)
                data["scheme"] = scheme_list
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})


class CustomProductHomeViewSet(viewsets.GenericViewSet):
    """
    add_custom:个性化定制提交
    """

    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = CustomProductHomeCreateSerializer

    @action(["post"], detail=True)
    def add_custom(self, request, *args, **kwargs):
        try:
            consumer = request.user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            electron_ids = serializer.data["electron_id"]
            scheme_ids = serializer.data["scheme_id"]
            custom_product = CustomProduct()
            custom_product.consumer = consumer
            custom_product.product_id = int(kwargs["pk"])
            custom_product.appearance = serializer.data["appearance"]
            custom_product.factory = serializer.data["factory"]
            custom_product.save()

            # 保存提交的个性化定制元器件
            if electron_ids:
                try:
                    for electron_id in electron_ids:
                        custom_electron = CustomProductElectron()
                        electron = Electron.objects.get(id=int(electron_id))
                        custom_electron.custom_product = custom_product
                        custom_electron.electron_id = int(electron_id)
                        custom_electron.model_name = electron.model_name
                        custom_electron.save()
                except Exception as e:
                    if custom_product.electrons_custom.all():
                        for electron_custom in custom_product.electrons_custom.all():
                            CustomProductElectron.objects.filter(id=electron_custom.id).delete()
                    CustomProduct.objects.filter(id=custom_product.id).delete()
                    return Response({"error": "保存个性化定制元器件失败!", "error_message": e.args})

            # 保存提交的个性化定制方案
            if scheme_ids:
                try:
                    for scheme_id in scheme_ids:
                        custom_scheme = CustomProductScheme()
                        scheme = Scheme.objects.get(id=int(scheme_id))
                        custom_scheme.custom_product = custom_product
                        custom_scheme.scheme_id = int(scheme_id)
                        custom_scheme.scheme_name = scheme.title
                        custom_scheme.save()
                except Exception as e:
                    if custom_product.schemes_custom.all():
                        for scheme_custom in custom_product.schemes_custom.all():
                            CustomProductScheme.objects.filter(id=scheme_custom.id).delete()
                    if custom_product.electrons_custom.all():
                        for electron_custom in custom_product.electrons_custom.all():
                            CustomProductElectron.objects.filter(id=electron_custom.id).delete()
                    CustomProduct.objects.filter(id=custom_product.id).delete()
                    return Response({"error": "保存个性化定制方案失败!", "error_message": e.args})

            return Response({"success": "个性化定制提交成功"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"fail": "个性化定制提交失败!", "error_message": e.args}, status=status.HTTP_201_CREATED)


class CustomProductUserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """提交个性化定制前用户信息完善"""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    serializer_class = CustomProductUserSerializer

    def get_object(self):
        return self.request.user


class CommentViewSet(viewsets.GenericViewSet):
    """
    用户评论
    cmlist:获取已有评论
    amadd:用户提交评论
    """
    queryset = UniversalComment.objects.all()
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == "cmlist":
            return CommentListSerializer
        elif self.action == "cmadd":
            return CommentCreateSerializer
        else:
            return CommentListSerializer

    def get_permissions(self):
        if self.action == "cmadd":
            return [IsAuthenticated()]
        elif self.action == "cmlist":
            return []
        return []

    @action(['get'], detail=True)
    def cmlist(self, request, *args, **kwargs):
        try:
            queryset = UniversalComment.objects.filter(universal_id=int(kwargs['pk']), type=self.request.query_params["type"])

            page = self.paginate_queryset(queryset.order_by('-create_at'))
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})

    @action(['post'], detail=True)
    def cmadd(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            consumer = request.user
            comment = UniversalComment()
            comment.consumer = consumer
            comment.type = self.request.query_params["type"]
            comment.universal_id = kwargs["pk"]
            comment.content = serializer.data["content"]
            comment.save()
            return Response({"success": "评论成功!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": e})




