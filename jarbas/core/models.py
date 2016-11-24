from django.db import models
from requests import head


class Document(models.Model):

    document_id = models.IntegerField('Document ID', db_index=True)
    congressperson_name = models.CharField('Congressperson name', max_length=33)
    congressperson_id = models.IntegerField('Congressperson ID', db_index=True)
    congressperson_document = models.IntegerField('Congressperson document')
    term = models.IntegerField('Term', db_index=True)
    state = models.CharField('State', max_length=2)
    party = models.CharField('Party', db_index=True, max_length=7)
    term_id = models.IntegerField('Term ID')
    subquota_number = models.IntegerField('Subquote ID', db_index=True)
    subquota_description = models.CharField('Subquota descrition', max_length=128)
    subquota_group_id = models.IntegerField('Subquota group ID', db_index=True)
    subquota_group_description = models.CharField('Subquota group description', max_length=20)
    supplier = models.CharField('Supplier', max_length=100)
    cnpj_cpf = models.CharField('CNPJ or CPF', db_index=True, max_length=14)
    document_number = models.CharField('Document number', max_length=30)
    document_type = models.IntegerField('Document type', db_index=True)
    issue_date = models.DateTimeField('Issue date', blank=True, null=True)
    document_value = models.DecimalField('Document value', max_digits=10, decimal_places=3)
    remark_value = models.DecimalField('Remark value', max_digits=10, decimal_places=3)
    net_value = models.DecimalField('Net value', max_digits=10, decimal_places=3)
    month = models.IntegerField('Month', db_index=True)
    year = models.IntegerField('Year', db_index=True)
    installment = models.IntegerField('Installment')
    passenger = models.CharField('Passenger', max_length=59)
    leg_of_the_trip = models.CharField('Leg of the trip', max_length=100)
    batch_number = models.IntegerField('Batch number')
    reimbursement_number = models.IntegerField('Reimbursement number', db_index=True)
    reimbursement_value = models.DecimalField('Reimbusrsement value', max_digits=10, decimal_places=3)
    applicant_id = models.IntegerField('Applicant ID', db_index=True)


class Receipt(models.Model):

    url = models.URLField('URL', null=True, blank=True, default=None, max_length=128)
    fetched = models.BooleanField('Was fetched?', default=False)
    document = models.OneToOneField(Document, on_delete=models.CASCADE)

    def get_url(self):
        server = 'www.camara.gov.br'
        path = 'cota-parlamentar/documentos/publ/{}/{}/{}.pdf'.format(
            self.document.applicant_id,
            self.document.year,
            self.document.document_id
        )
        return 'http://{}/{}'.format(server, path)

    def fetch_url(self):
        if self.url:
            return self.url

        probable_url = self.get_url()
        status = head(probable_url).status_code
        url = probable_url if 200 <= status < 400 else None

        self.url = url
        self.fetched = True
        self.save()

        return url


class Activity(models.Model):

    code = models.CharField('Code', max_length=10)
    description = models.CharField('Description', max_length=167)


class Supplier(models.Model):

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
