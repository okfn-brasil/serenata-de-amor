from django.db import models


class Activity(models.Model):

    code = models.CharField('Code', max_length=10)
    description = models.CharField('Description', max_length=167)


class Company(models.Model):

    cnpj = models.CharField('CNPJ', db_index=True, max_length=18)
    opening = models.DateField('Opening date', blank=True, null=True)

    legal_entity = models.CharField('Legal entity', blank=True, null=True, max_length=72)
    trade_name = models.CharField('Trade name', blank=True, null=True, max_length=55)
    name = models.CharField('Name', blank=True, null=True, max_length=144)
    type = models.CharField('Type', blank=True, null=True, max_length=6)

    main_activity = models.ManyToManyField(Activity, related_name='main')
    secondary_activity = models.ManyToManyField(Activity, related_name='secondary')

    status = models.CharField('Status', blank=True, null=True, max_length=5)
    situation = models.CharField('Situation', blank=True, null=True, max_length=8)
    situation_reason = models.CharField('Situation reason', blank=True, null=True, max_length=44)
    situation_date = models.DateField('Situation date', blank=True, null=True)
    special_situation = models.CharField('Special situation', blank=True, null=True, max_length=51)
    special_situation_date = models.DateField('Special situation date', blank=True, null=True)
    responsible_federative_entity = models.CharField('Responsible federative entity', blank=True, null=True, max_length=38)

    address = models.CharField('Address', blank=True, null=True, max_length=64)
    number = models.CharField('Number', blank=True, null=True, max_length=6)
    additional_address_details = models.CharField('Additional address details', blank=True, null=True, max_length=143)
    neighborhood = models.CharField('Neighborhood', blank=True, null=True, max_length=50)
    zip_code = models.CharField('Zip code', blank=True, null=True, max_length=10)
    city = models.CharField('City', blank=True, null=True, max_length=32)
    state = models.CharField('State', blank=True, null=True, max_length=2)
    email = models.EmailField('Email', blank=True, null=True, max_length=58)
    phone = models.CharField('Phone', blank=True, null=True, max_length=32)

    latitude = models.DecimalField('Latitude', decimal_places=7, max_digits=10, blank=True, null=True)
    longitude = models.DecimalField('Longitude', decimal_places=7, max_digits=10, blank=True, null=True)

    last_updated = models.DateTimeField('Last updated', blank=True, null=True)
