from celery import shared_task

from jarbas.core.models import Reimbursement


@shared_task
def create_or_update_reimbursement(data):
    """
    :param data: (dict) reimbursement data (keys and data types must mach
    Reimbursement model)
    """
    kwargs = dict(document_id=data['document_id'], defaults=data)
    Reimbursement.objects.update_or_create(**kwargs)
