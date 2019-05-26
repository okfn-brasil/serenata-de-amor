from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ReimbursementListPagination(PageNumberPagination):
    """Paginator to show the total amount of reimbursements"""
    def get_paginated_response(self, data):
        return Response({
            'summary': self.get_total_net_value(data),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

    def get_total_net_value(self, data):
        """Calculates the sum of reimbursements"""
        summary = {
            'count': self.page.paginator.count,
            'total_positive': sum([obj['total_net_value'] if obj['total_net_value'] >= 0 else 0 for obj in data]),
            'total_negative': sum([obj['total_net_value'] if obj['total_net_value'] < 0 else 0 for obj in data])
        }

        summary['total_net'] = summary['total_positive'] + summary['total_negative']

        return summary
