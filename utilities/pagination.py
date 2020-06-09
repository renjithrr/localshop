from rest_framework.pagination import LimitOffsetPagination
from .mixins import ResponseViewMixin


class CustomOffsetPagination(LimitOffsetPagination, ResponseViewMixin):
    default_limit = 10
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 1000

    def success_response(self, data):
        return self.jp_response(
        headers='HTTP_200_OK',
        data={
        'data': data,
        'links': {
        'next': self.get_next_link(),
        'previous': self.get_previous_link()
        }, 'count': self.count,
        }
        )
