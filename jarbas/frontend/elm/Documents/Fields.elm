module Documents.Fields exposing (getLabel, isSearchable, labels, names, sets)

import Dict
import Internationalization exposing (Language(..), TranslationId(..), translate)


names : List String
names =
    [ "document_id"
    , "congressperson_name"
    , "congressperson_id"
    , "congressperson_document"
    , "term"
    , "state"
    , "party"
    , "term_id"
    , "subquota_number"
    , "subquota_description"
    , "subquota_group_id"
    , "subquota_group_description"
    , "supplier"
    , "cnpj_cpf"
    , "document_number"
    , "document_type"
    , "issue_date"
    , "document_value"
    , "remark_value"
    , "net_value"
    , "month"
    , "year"
    , "installment"
    , "passenger"
    , "leg_of_the_trip"
    , "batch_number"
    , "reimbursement_number"
    , "reimbursement_value"
    , "applicant_id"
    ]


labels : Language -> List String
labels lang =
    List.map
        (\f -> translate lang f)
        [ FieldDocumentId
        , FieldCongresspersonName
        , FieldCongresspersonId
        , FieldCongresspersonDocument
        , FieldTerm
        , FieldState
        , FieldParty
        , FieldTermId
        , FieldSubquotaNumber
        , FieldSubquotaDescription
        , FieldSubquotaGroupId
        , FieldSubquotaGroupDescription
        , FieldSupplier
        , FieldCNPJOrCPF
        , FieldDocumentNumber
        , FieldDocumentType
        , FieldIssueDate
        , FieldDocumentValue
        , FieldRemarkValue
        , FieldNetValue
        , FieldMonth
        , FieldYear
        , FieldInstallment
        , FieldPassenger
        , FieldLegOfTheTrip
        , FieldBatchNumber
        , FieldReimbursementNumber
        , FieldReimbursementValue
        , FieldApplicantId
        ]


getLabel : Language -> String -> String
getLabel lang name =
    List.map2 (,) names (labels lang)
        |> Dict.fromList
        |> Dict.get name
        |> Maybe.withDefault ""


isSearchable : ( String, String ) -> Bool
isSearchable ( field, label ) =
    if field == "page" then
        True
    else
        List.member field
            [ "applicant_id"
            , "cnpj_cpf"
            , "congressperson_id"
            , "document_id"
            , "document_type"
            , "month"
            , "party"
            , "reimbursement_number"
            , "state"
            , "subquota_group_id"
            , "subquota_number"
            , "term"
            , "year"
            ]


sets : Language -> List ( Int, ( String, List String ) )
sets lang =
    List.indexedMap
        (,)
        [ ( translate lang SearchFieldsetReimbursement
          , [ "document_id"
            , "document_type"
            , "applicant_id"
            , "reimbursement_number"
            , "subquota_number"
            , "subquota_group_id"
            ]
          )
        , ( translate lang SearchFieldsetCongressperson
          , [ "congressperson_id"
            , "party"
            , "state"
            , "term"
            ]
          )
        , ( translate lang SearchFieldsetExpense
          , [ "cnpj_cpf"
            , "year"
            , "month"
            ]
          )
        ]
