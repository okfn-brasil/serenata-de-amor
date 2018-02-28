from django.conf.urls import url

from jarbas.chamber_of_deputies.views import (
    ReimbursementListView,
    ReimbursementDetailView,
    ReceiptDetailView,
    SameDayReimbursementListView,
    ApplicantListView,
    SubquotaListView,
)


urlpatterns = [
    url(
        r'^reimbursement/$',
        ReimbursementListView.as_view(),
        name='reimbursement-list'
    ),
    url(
        r'^reimbursement/(?P<document_id>\d+)/$',
        ReimbursementDetailView.as_view(),
        name='reimbursement-detail'
    ),
    url(
        r'^reimbursement/(?P<document_id>\d+)/receipt/$',
        ReceiptDetailView.as_view(),
        name='reimbursement-receipt'
    ),
    url(
        r'^reimbursement/(?P<document_id>\d+)/same_day/$',
        SameDayReimbursementListView.as_view(),
        name='reimbursement-same-day'
    ),
    url(r'^applicant/$', ApplicantListView.as_view(), name='applicant-list'),
    url(r'^subquota/$', SubquotaListView.as_view(), name='subquota-list')
]
