from datetime import date
from random import randrange
from django.utils import timezone

from jarbas.chamber_of_deputies.models import Tweet


suspicions = {
    'over_monthly_subquota': {'is_suspect': True, 'probability': 1.0}
}

sample_reimbursement_data = dict(
    applicant_id=13,
    batch_number=9,
    cnpj_cpf='11111111111111',
    congressperson_document=2,
    congressperson_id=1,
    congressperson_name='Roger That',
    document_id=42,
    document_number='6',
    document_type=7,
    document_value=8.90,
    installment=7,
    issue_date=date(1970, 1, 1),
    leg_of_the_trip='8',
    month=1,
    net_values='1.99,2.99',
    party='Partido',
    passenger='John Doe',
    reimbursement_numbers='10,11',
    reimbursement_values='12.13,14.15',
    remark_value=1.23,
    state='UF',
    subquota_description='Subquota description',
    subquota_group_description='Subquota group desc',
    subquota_group_id=5,
    subquota_id=4,
    supplier='Acme',
    term=1970,
    term_id=3,
    total_net_value=4.56,
    total_reimbursement_value=None,
    year=1970,
    probability=0.5,
    suspicions=suspicions
)


def random_tweet_status():
    """
    Fixture generators (mixer, and faker behind the scenes) won't generate a
    value for a `DecimalField` with zero decimal places - which is the case of
    Tweet.status (too big to fit `BigIntegerField`). Therefore we use this
    function to workaround random test fixtures for Tweet.status.
    """
    status = Tweet._meta.get_field('status')
    min_range = 9223372036854775807  # max big integer should be the minimum
    max_range = 10 ** status.max_digits  # field limit
    return randrange(min_range, max_range)


def get_sample_reimbursement_api_response(obj):

    # freezegun API to return timezone aware objects is not simple
    last_update_naive = timezone.make_naive(obj.last_update)

    return dict(
        applicant_id=obj.applicant_id,
        batch_number=obj.batch_number,
        cnpj_cpf=obj.cnpj_cpf,
        congressperson_document=obj.congressperson_document,
        congressperson_id=obj.congressperson_id,
        congressperson_name=obj.congressperson_name,
        document_id=obj.document_id,
        document_number=obj.document_number,
        document_type=obj.document_type,
        document_value=float(obj.document_value),
        installment=obj.installment,
        issue_date=obj.issue_date.strftime('%Y-%m-%d'),
        leg_of_the_trip=obj.leg_of_the_trip,
        month=obj.month,
        party=obj.party,
        passenger=obj.passenger,
        all_reimbursement_numbers=obj.all_reimbursement_numbers,
        all_reimbursement_values=obj.all_reimbursement_values,
        all_net_values=obj.all_net_values,
        remark_value=obj.remark_value,
        state=obj.state,
        subquota_description=obj.subquota_description,
        subquota_group_description=obj.subquota_group_description,
        subquota_group_id=obj.subquota_group_id,
        subquota_id=obj.subquota_id,
        supplier=obj.supplier,
        term=obj.term,
        term_id=obj.term_id,
        total_net_value=float(obj.total_net_value),
        total_reimbursement_value=obj.total_reimbursement_value,
        year=obj.year,
        probability=obj.probability,
        suspicions=obj.suspicions,
        receipt_text=obj.receipt_text,
        last_update=last_update_naive.strftime('%Y-%m-%dT%H:%M:%S-03:00'),
        available_in_latest_dataset=obj.available_in_latest_dataset,
        receipt=dict(fetched=obj.receipt_fetched, url=obj.receipt_url),
        search_vector=None
    )
