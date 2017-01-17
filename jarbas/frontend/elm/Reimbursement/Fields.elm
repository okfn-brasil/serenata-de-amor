module Reimbursement.Fields exposing (..)

import Internationalization exposing (Language(..), TranslationId(..), translate)


names : List String
names =
    [ "year"
    , "documentId"
    , "applicantId"
    , "totalReimbursementValue"
    , "totalNetValue"
    , "reimbursementNumbers"
    , "netValues"
    , "congresspersonId"
    , "congresspersonName"
    , "congresspersonDocument"
    , "state"
    , "party"
    , "termId"
    , "term"
    , "subquotaId"
    , "subquotaDescription"
    , "subquotaGroupId"
    , "subquotaGroupDescription"
    , "supplier"
    , "cnpjCpf"
    , "documentType"
    , "documentNumber"
    , "documentValue"
    , "issueDate"
    , "issueDateStart"
    , "issueDateEnd"
    , "month"
    , "remarkValue"
    , "installment"
    , "batchNumber"
    , "reimbursementValues"
    , "passenger"
    , "legOfTheTrip"
    , "probability"
    , "suspicions"
    ]


labels : List TranslationId
labels =
    [ FieldYear
    , FieldDocumentId
    , FieldApplicantId
    , FieldTotalReimbursementValue
    , FieldTotalNetValue
    , FieldReimbursementNumbers
    , FieldNetValues
    , FieldCongresspersonId
    , FieldCongresspersonName
    , FieldCongresspersonDocument
    , FieldState
    , FieldParty
    , FieldTermId
    , FieldTerm
    , FieldSubquotaId
    , FieldSubquotaDescription
    , FieldSubquotaGroupId
    , FieldSubquotaGroupDescription
    , FieldCompany
    , FieldCnpjCpf
    , FieldDocumentType
    , FieldDocumentNumber
    , FieldDocumentValue
    , FieldIssueDate
    , FieldIssueDateStart
    , FieldIssueDateEnd
    , FieldMonth
    , FieldRemarkValue
    , FieldInstallment
    , FieldBatchNumber
    , FieldReimbursementValues
    , FieldPassenger
    , FieldLegOfTheTrip
    , FieldProbability
    , FieldSuspicions
    ]


{-| Filter to get searchable fields:

    >>> isSearchable ( "year", "2016" )
    True

    >>> isSearchable ( "format", "json" )
    False

-}
isSearchable : ( String, a ) -> Bool
isSearchable ( field, _ ) =
    if field == "page" then
        True
    else
        List.member field
            [ "applicantId"
            , "cnpjCpf"
            , "documentId"
            , "issueDateEnd"
            , "issueDateStart"
            , "month"
            , "subquotaId"
            , "year"
            ]


sets : List ( Int, ( TranslationId, List String ) )
sets =
    List.indexedMap (,)
        [ ( SearchFieldsetCongressperson
          , [ "applicantId"
            , "year"
            , "month"
            , "subquotaId"
            , "cnpjCpf"
            , "issueDateStart"
            , "issueDateEnd"
            ]
          )
        , ( SearchFieldsetReimbursement
          , [ "applicantId", "year", "documentId" ]
          )
        ]


{-| Filter to get numbers only fields:

    >>> isNumeric "year"
    True

    >>> isNumeric "format"
    False

-}
isNumeric : String -> Bool
isNumeric field =
    List.member field
        [ "applicantId"
        , "cnpjCpf"
        , "congresspersonId"
        , "documentId"
        , "month"
        , "subquotaId"
        , "year"
        ]


isDate : String -> Bool
isDate field =
    List.member field
        [ "issueDateStart"
        , "issueDateEnd"
        ]
