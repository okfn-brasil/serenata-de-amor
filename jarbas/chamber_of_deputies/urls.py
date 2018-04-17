from django.urls import path

from jarbas.chamber_of_deputies.views import (
    ReimbursementListView,
    ReimbursementDetailView,
    ReceiptDetailView,
    SameDayReimbursementListView,
    ApplicantListView,
    SubquotaListView,
)


app_name = 'chamber_of_deputies'

urlpatterns = [
    path(
        'reimbursement/',
        ReimbursementListView.as_view(),
        name='reimbursement-list'
    ),
    path(
        'reimbursement/<int:document_id>/',
        ReimbursementDetailView.as_view(),
        name='reimbursement-detail'
    ),
    path(
        'reimbursement/<int:document_id>/receipt/',
        ReceiptDetailView.as_view(),
        name='reimbursement-receipt'
    ),
    path(
        'reimbursement/<int:document_id>/same_day/',
        SameDayReimbursementListView.as_view(),
        name='reimbursement-same-day'
    ),
    path('applicant/', ApplicantListView.as_view(), name='applicant-list'),
    path('subquota/', SubquotaListView.as_view(), name='subquota-list')
]
