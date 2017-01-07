module Documents.Fields exposing (..)

import Dict
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


labels : Language -> List String
labels lang =
    List.map
        (\f -> translate lang f)
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


getLabel : Language -> String -> String
getLabel lang name =
    List.map2 (,) names (labels lang)
        |> Dict.fromList
        |> Dict.get name
        |> Maybe.withDefault ""


{-| Filter to get searchable fields:

    >>> isSearchable ( "year", "2016" )
    True

    >>> isSearchable ( "format", "json" )
    False

-}
isSearchable : ( String, String ) -> Bool
isSearchable ( field, label ) =
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


sets : Language -> List ( Int, ( String, List String ) )
sets lang =
    List.indexedMap
        (,)
        [ ( translate lang SearchFieldsetCongressperson
          , [ "applicantId"
            , "year"
            , "month"
            , "subquotaId"
            , "cnpjCpf"
            , "issueDateStart"
            , "issueDateEnd"
            ]
          )
        , ( translate lang SearchFieldsetReimbursement
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
