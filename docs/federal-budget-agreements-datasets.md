### Federal Budget - Agreements and Amendments

The Brazilian Constitution allows each parliamentary to allocate a portion of the federal budget for a specific purpose.
But there is a issue that the law also allows the parliamentary indicates the institution (NGO, Association, Foundation, 
public agency) that will receive the money. 
This creates a major risk of embezzlement, if the money is intended to entities controlled by the parlamentary itself or
 such entities are blacklisted and shouldn't work to or with the government.

The federal government publishes the list of thoses entities that received funds by amendments created by 
congresspersons to allocate the federal budget. The files can be dowloaded from 
[Portal de Convênios - SICONV](http://portal.convenios.gov.br/download-de-dados).

A portuguese version of the data dictionary is avaiable [here](http://portal.convenios.gov.br/images/docs/CGSIS/siconv_dicionario_dados.pdf).

The data model is also avaiable [here](http://portal.convenios.gov.br/images/docs/CGSIS/Modelo_de_Dados_SICONV_v3.jpg).

Bellow is the list of files/datasets downloaded from SICONV that are related to agreements, amendments and payments 
using federal budget.


#### Agreements (Todo)

* Amendments Dataset fields:
    * **agreement_number**: 
    * **proposal_id**: 
    * **day_signed**: 
    * **month_signed**: 
    * **year_signed**: 
    * **date_signed**: 
    * **situtaion**: 
    * **subsituation**: 
    * **publication_situation**: 
    * **active**: 
    * **obtv_indicative**: 
    * **process_number**: 
    * **published_date**: 
    * **agreement_start_date**: 
    * **agreement_end_date**: 
    * **accountability_date**: 
    * **accountability_deadline**: 
    * **quantity_instrument_signeds**: 
    * **additives_quantity**: 
    * **legal_extensions**: 
    * **total_value**: 
    * **federeal_government_contribution**: 
    * **counterparty_value**: 
    * **value_commited**: 
    * **value_disbursed**: 
    * **returned_value_at_end**: 
    * **returned_value_to_convenient_at_end**: 
    * **counterparty_value**: 
        
        
#### Amendments
This dataset indicates which entity received the money and what was the congressman who was the 
author of the amendment.

* Amendments Dataset fields:
    * **proposal_id**: Sequecial code created by system (SICONV) to a proposal.
    * **proponent_qualification**: Proponent qualification.
    * **amendment_program_code**: Key that identifies the program, composed of: (Organ Code+Year+Sequencial Code).
    * **amendment_number**: Congress amendment number.
    * **congressperson_name**: Congressperson name.
    * **amendment_beneficiary**: CNPJ of the Beneficiary (Proponent) of the amendment.
    * **tax_indicative**: Indicative of Tax Budget (Congressperson type equal to INDIVIDUAL + Proposal Registration Year >= 2014). Types: yes, no.
    * **congressperson_type**: Type of cogressperson: Committee, Individual, Seat
    * **amendment_proposal_tranfer_value**: Amendment's value registered in the proposal.
    * **amendment_tranfer_value**: Amendment's value signed.