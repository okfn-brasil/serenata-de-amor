from django.conf.urls import url

from jarbas.api.views import (
    ApplicantListView,
    DocumentViewSet,
    ReceiptDetailView,
    ReceiptViewSet,
    ReimbursementDetailView,
    ReimbursementListView,
    SubquotaListView,
    SupplierViewSet
)


urlpatterns = [

    url(
        r'^reimbursement(?:/(?P<year>\d{4}))?(?:/(?P<applicant_id>\d+))?/$',
        ReimbursementListView.as_view(),
        name='reimbursement-list'
    ),

    url(
        r'^reimbursement/(?P<year>\d{4})/(?P<applicant_id>\d+)/(?P<document_id>\d+)/$',
        ReimbursementDetailView.as_view(),
        name='reimbursement-detail'
    ),


    url(
        r'^reimbursement/(?P<year>\d{4})/(?P<applicant_id>\d+)/(?P<document_id>\d+)/receipt/$',
        ReceiptDetailView.as_view(),
        name='reimbursement-receipt'
    ),

    url(r'^applicant/$', ApplicantListView.as_view(), name='applicant-list'),
    url(r'^subquota/$', SubquotaListView.as_view(), name='subquota-list'),

    url(r'^document/$', DocumentViewSet.as_view({'get': 'list'}), name='document-list'),
    url(r'^supplier/(?P<pk>\d+)/$', SupplierViewSet.as_view({'get': 'retrieve'}), name='supplier-detail'),
    url(r'^receipt/(?P<pk>\d+)/$', ReceiptViewSet.as_view({'get': 'retrieve'}), name='receipt-detail')
]
