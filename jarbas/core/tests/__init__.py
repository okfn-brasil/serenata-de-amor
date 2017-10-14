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

sample_activity_data = dict(
    code='42',
    description='So long, so long, and thanks for all the fish'
)

sample_company_data = dict(
    cnpj='12.345.678/9012-34',
    opening=date(1995, 9, 27),
    legal_entity='42 - The answer to life, the universe, and everything',
    trade_name="Don't panic",
    name='Do not panic, sir',
    type='BOOK',
    status='OK',
    situation='EXISTS',
    situation_reason='Douglas Adams wrote it',
    situation_date=date(2016, 9, 25),
    special_situation='WE LOVE IT',
    special_situation_date=date(1997, 9, 28),
    responsible_federative_entity='Vogons',
    address='Earth',
    number='',
    additional_address_details='',
    neighborhood='',
    zip_code='',
    city='',
    state='',
    email='',
    phone='',
    last_updated=timezone.now(),
    latitude=None,
    longitude=None
)


def random_tweet_status():
    """
    Fixture generators (mixer, and faker behind the scenes) won't generate a
    value for a `DecimalField` with zero decimal places — which is the case of
    Tweet.status (too big to fit `BigIntegerField`). Therefore we use this
    function to workaround random test fixtures for Tweet.status.
    """
    status = Tweet._meta.get_field('status')
    min_range = 9223372036854775807  # max big integer should be the minimum
    max_range = 10 ** status.max_digits  # field limit
    return randrange(min_range, max_range)
