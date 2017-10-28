from datetime import date

from django.utils import timezone


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
