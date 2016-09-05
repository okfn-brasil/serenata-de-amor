import json

from django.core.serializers import serialize
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from serenata.core.models import Document


def document(request, document_id):
    document =  get_object_or_404(Document, document_id=document_id)
    serialized = json.loads(serialize('json', [document]))
    return JsonResponse(serialized[0]['fields'])
