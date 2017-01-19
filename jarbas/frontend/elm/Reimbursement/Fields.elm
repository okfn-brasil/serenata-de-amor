module Reimbursement.Fields exposing (..)

import Internationalization exposing (Language(..), TranslationId(..), translate)
import List.Extra


type Field
    = Field Label String


type Label
    = Year
    | DocumentId
    | ApplicantId
    | TotalReimbursementValue
    | TotalNetValue
    | ReimbursementNumbers
    | NetValues
    | CongresspersonId
    | CongresspersonName
    | CongresspersonDocument
    | State
    | Party
    | TermId
    | Term
    | SubquotaId
    | SubquotaDescription
    | SubquotaGroupId
    | SubquotaGroupDescription
    | Company
    | CnpjCpf
    | DocumentType
    | DocumentNumber
    | DocumentValue
    | IssueDate
    | IssueDateStart
    | IssueDateEnd
    | Month
    | RemarkValue
    | Installment
    | BatchNumber
    | ReimbursementValues
    | Passenger
    | LegOfTheTrip
    | Probability
    | Suspicions
    | Empty


searchableLabels : List ( Label, String )
searchableLabels =
    [ ( ApplicantId, "ApplicantId" )
    , ( CnpjCpf, "CnpjCpf" )
    , ( DocumentId, "DocumentId" )
    , ( IssueDateEnd, "IssueDateEnd" )
    , ( IssueDateStart, "IssueDateStart" )
    , ( Month, "Month" )
    , ( SubquotaId, "SubquotaId" )
    , ( Year, "Year" )
    ]


allLabels : List Label
allLabels =
    [ Year, DocumentId, ApplicantId, TotalReimbursementValue, TotalNetValue, ReimbursementNumbers, NetValues, CongresspersonId, CongresspersonName, CongresspersonDocument, State, Party, TermId, Term, SubquotaId, SubquotaDescription, SubquotaGroupId, SubquotaGroupDescription, Company, CnpjCpf, DocumentType, DocumentNumber, DocumentValue, IssueDate, IssueDateStart, IssueDateEnd, Month, RemarkValue, Installment, BatchNumber, ReimbursementValues, Passenger, LegOfTheTrip, Probability, Suspicions ]


labelToUrl : Label -> String
labelToUrl label =
    List.Extra.find (Tuple.first >> (==) label) searchableLabels
        |> Maybe.map (Tuple.second)
        |> Maybe.withDefault ""


urlToLabel : String -> Label
urlToLabel url =
    List.Extra.find (Tuple.second >> (==) url) searchableLabels
        |> Maybe.map (Tuple.first)
        |> Maybe.withDefault Empty


sets : List ( Int, ( TranslationId, List Label ) )
sets =
    List.indexedMap (,)
        [ ( SearchFieldsetCongressperson
          , [ ApplicantId
            , Year
            , Month
            , SubquotaId
            , CnpjCpf
            , IssueDateStart
            , IssueDateEnd
            ]
          )
        , ( SearchFieldsetReimbursement
          , [ ApplicantId, Year, DocumentId ]
          )
        ]


{-| Filter to get numbers only fields:

    >>> isNumeric "year"
    True

    >>> isNumeric "format"
    False

-}
isNumeric : Label -> Bool
isNumeric label =
    case label of
        ApplicantId ->
            True

        CnpjCpf ->
            True

        CongresspersonId ->
            True

        DocumentId ->
            True

        Month ->
            True

        SubquotaId ->
            True

        Year ->
            True

        _ ->
            False


isDate : Label -> Bool
isDate label =
    case label of
        IssueDateStart ->
            True

        IssueDateEnd ->
            True

        _ ->
            False


getValue : Field -> String
getValue (Field _ value) =
    value


getLabel : Field -> Label
getLabel (Field label _) =
    label


getLabelTranslation : Language -> Field -> String
getLabelTranslation language (Field label _) =
    let
        translationId =
            case label of
                Year ->
                    FieldYear

                DocumentId ->
                    FieldDocumentId

                ApplicantId ->
                    FieldApplicantId

                TotalReimbursementValue ->
                    FieldTotalReimbursementValue

                TotalNetValue ->
                    FieldTotalNetValue

                ReimbursementNumbers ->
                    FieldReimbursementNumbers

                NetValues ->
                    FieldNetValues

                CongresspersonId ->
                    FieldCongresspersonId

                CongresspersonName ->
                    FieldCongresspersonName

                CongresspersonDocument ->
                    FieldCongresspersonDocument

                State ->
                    FieldState

                Party ->
                    FieldParty

                TermId ->
                    FieldTermId

                Term ->
                    FieldTerm

                SubquotaId ->
                    FieldSubquotaId

                SubquotaDescription ->
                    FieldSubquotaDescription

                SubquotaGroupId ->
                    FieldSubquotaGroupId

                SubquotaGroupDescription ->
                    FieldSubquotaGroupDescription

                Company ->
                    FieldCompany

                CnpjCpf ->
                    FieldCnpjCpf

                DocumentType ->
                    FieldDocumentType

                DocumentNumber ->
                    FieldDocumentNumber

                DocumentValue ->
                    FieldDocumentValue

                IssueDate ->
                    FieldIssueDate

                IssueDateStart ->
                    FieldIssueDateStart

                IssueDateEnd ->
                    FieldIssueDateEnd

                Month ->
                    FieldMonth

                RemarkValue ->
                    FieldRemarkValue

                Installment ->
                    FieldInstallment

                BatchNumber ->
                    FieldBatchNumber

                ReimbursementValues ->
                    FieldReimbursementValues

                Passenger ->
                    FieldPassenger

                LegOfTheTrip ->
                    FieldLegOfTheTrip

                Probability ->
                    FieldProbability

                Suspicions ->
                    FieldSuspicions

                Empty ->
                    EmptyField
    in
        translate language translationId
