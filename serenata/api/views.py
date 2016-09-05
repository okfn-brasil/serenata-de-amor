import json

from django.core.serializers import serialize
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404

from serenata.core.models import Document


def document(request, document_id):

    # query & serialize
    document = get_object_or_404(Document, document_id=document_id)
    serialized = json.loads(serialize('json', [document]))
    try:
        obj = serialized[0]['fields']
    except (IndexError, KeyError):
        raise Http404("Couldn't serialize document " + document.document_id)

    # convert DecimalField to Float
    float_fields = (
        'document_value',
        'remark_value',
        'net_value',
        'reimbursement_value'
    )
    for float_field in float_fields:
        obj[float_field] = float(obj[float_field])

    return JsonResponse(obj)
