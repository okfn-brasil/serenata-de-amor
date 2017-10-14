from datetime import date
from random import randrange

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
