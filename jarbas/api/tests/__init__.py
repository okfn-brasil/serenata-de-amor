from django.utils import timezone


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
