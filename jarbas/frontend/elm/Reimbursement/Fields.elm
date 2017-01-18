module Reimbursement.Fields exposing (..)

import Internationalization exposing (Language(..), TranslationId(..), translate)


type Field
    = Field Label String


type Label
    = Label TranslationId String


labels : List Label
labels =
    [ Label FieldYear "year"
    , Label FieldDocumentId "documentId"
    , Label FieldApplicantId "applicantId"
    , Label FieldTotalReimbursementValue "totalReimbursementValue"
    , Label FieldTotalNetValue "totalNetValue"
    , Label FieldReimbursementNumbers "reimbursementNumbers"
    , Label FieldNetValues "netValues"
    , Label FieldCongresspersonId "congresspersonId"
    , Label FieldCongresspersonName "congresspersonName"
    , Label FieldCongresspersonDocument "congresspersonDocument"
    , Label FieldState "state"
    , Label FieldParty "party"
    , Label FieldTermId "termId"
    , Label FieldTerm "term"
    , Label FieldSubquotaId "subquotaId"
    , Label FieldSubquotaDescription "subquotaDescription"
    , Label FieldSubquotaGroupId "subquotaGroupId"
    , Label FieldSubquotaGroupDescription "subquotaGroupDescription"
    , Label FieldCompany "supplier"
    , Label FieldCnpjCpf "cnpjCpf"
    , Label FieldDocumentType "documentType"
    , Label FieldDocumentNumber "documentNumber"
    , Label FieldDocumentValue "documentValue"
    , Label FieldIssueDate "issueDate"
    , Label FieldIssueDateStart "issueDateStart"
    , Label FieldIssueDateEnd "issueDateEnd"
    , Label FieldMonth "month"
    , Label FieldRemarkValue "remarkValue"
    , Label FieldInstallment "installment"
    , Label FieldBatchNumber "batchNumber"
    , Label FieldReimbursementValues "reimbursementValues"
    , Label FieldPassenger "passenger"
    , Label FieldLegOfTheTrip "legOfTheTrip"
    , Label FieldProbability "probability"
    , Label FieldSuspicions "suspicions"
    ]


{-| Filter to get searchable fields:

    >>> isSearchable ( "year", "2016" )
    True

    >>> isSearchable ( "format", "json" )
    False

-}
isSearchable : String -> Bool
isSearchable name =
    if name == "page" then
        True
    else
        List.member name
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
isNumeric name =
    List.member name
        [ "applicantId"
        , "cnpjCpf"
        , "congresspersonId"
        , "documentId"
        , "month"
        , "subquotaId"
        , "year"
        ]


isDate : String -> Bool
isDate name =
    List.member name
        [ "issueDateStart"
        , "issueDateEnd"
        ]


getValue : Field -> String
getValue (Field _ value) =
    value


getName : Field -> String
getName (Field (Label _ name) _) =
    name


getLabelTranslation : Language -> Field -> String
getLabelTranslation language (Field (Label translationId _) _) =
    translate language translationId
