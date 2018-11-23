from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class SupplierPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size'
    max_page_size = 10000

    # 自定义
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page': self.page.number
            },
            'results': data
        })


class ElectronPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size'
    max_page_size = 10000

    # 自定义
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'results': data
        })


class KwargsPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = 'page_size'
    max_page_size = 10000

    # 自定义
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page': self.page.number
            },
            'results': data
        })


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_query_param = "page"
    max_page_size = 1000

    # 自定义
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'results': data
        })


