from django.conf.urls import include, url

from jarbas.api.views import (
    DocumentViewSet,
    ReceiptViewSet,
    ReimbursementDetailView,
    ReimbursementListView,
    SupplierViewSet
)

# r'^reimbursement/(?P<year>\d{4}/(?P<applicant_id>\d+)/(?P<document_id>\d+)/$',
urlpatterns = [
    url(r'^reimbursement/', include([
        url(r'^$', ReimbursementListView.as_view(), name='reimbursement-list'),
        url(r'^(?P<year>\d{4})/', include([
            url(r'^$', ReimbursementListView.as_view(), name='reimbursement-by-year-list'),
            url(r'^(?P<applicant_id>\d+)/', include([
                url(r'^$', ReimbursementListView.as_view(), name='reimbursement-by-applicant-list'),
                url(r'^(?P<document_id>\d+)/$', ReimbursementDetailView.as_view(), name='reimbursement-detail')
            ]))
        ]))
    ])),

    url(r'^document/$', DocumentViewSet.as_view({'get': 'list'}), name='document-list'),
    url(r'^supplier/(?P<pk>\d+)/$', SupplierViewSet.as_view({'get': 'retrieve'}), name='supplier-detail'),
    url(r'^receipt/(?P<pk>\d+)/$', ReceiptViewSet.as_view({'get': 'retrieve'}), name='receipt-detail')
]
