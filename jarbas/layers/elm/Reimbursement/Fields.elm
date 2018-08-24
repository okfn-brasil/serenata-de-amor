module Reimbursement.Fields exposing (..)

import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..), TranslationSet)
import List.Extra


type Field
    = Field Label String


type Label
    = Year
    | DocumentId
    | ApplicantId
    | TotalValue
    | TotalNetValue
    | Numbers
    | CongresspersonId
    | Congressperson
    | CongresspersonName
    | CongresspersonDocument
    | State
    | Party
    | TermId
    | Term
    | SubquotaNumber
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
    | ClaimDate
    | Month
    | RemarkValue
    | Installment
    | BatchNumber
    | Passenger
    | LegOfTheTrip
    | Probability
    | Suspicions
    | Empty


searchableLabels : List ( Label, String )
searchableLabels =
    [ ( ApplicantId, "applicantId" )
    , ( CnpjCpf, "cnpjCpf" )
    , ( DocumentId, "documentId" )
    , ( IssueDateEnd, "issueDateEnd" )
    , ( IssueDateStart, "issueDateStart" )
    , ( Month, "month" )
    , ( SubquotaNumber, "subquotaNumber" )
    , ( Year, "year" )
    ]


allLabels : List Label
allLabels =
    [ Year, DocumentId, ApplicantId, TotalValue, TotalNetValue, Numbers, CongresspersonId, CongresspersonName, CongresspersonDocument, State, Party, TermId, Term, SubquotaNumber, SubquotaDescription, SubquotaGroupId, SubquotaGroupDescription, Company, CnpjCpf, DocumentType, DocumentNumber, DocumentValue, IssueDate, IssueDateStart, IssueDateEnd, Month, RemarkValue, Installment, BatchNumber, Passenger, LegOfTheTrip, Probability, Suspicions ]


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
            , SubquotaNumber
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

    isNumeric Year --> True

    isNumeric Company --> False

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

        SubquotaNumber ->
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


{-| Convert a field into what may be a search query:
    toQuery ( Field Year "2016" ) --> Just ( "year", "2016" )

    toQuery ( Field Year "" ) --> Nothing

    toQuery ( Field LegOfTheTrip "any" ) --> Nothing
-}
toQuery : Field -> Maybe ( String, String )
toQuery (Field label value) =
    let
        notEmpty =
            String.trim >> String.isEmpty >> not
    in
        if (notEmpty <| labelToUrl label) && (notEmpty value) then
            Just ( labelToUrl label, String.trim value )
        else
            Nothing


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

                TotalValue ->
                    FieldTotalValue

                TotalNetValue ->
                    FieldTotalNetValue

                Numbers ->
                    FieldNumbers

                CongresspersonId ->
                    FieldCongresspersonId

                Congressperson ->
                    FieldCongressperson

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

                SubquotaNumber ->
                    FieldSubquotaNumber

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

                ClaimDate ->
                    FieldClaimDate

                Month ->
                    FieldMonth

                RemarkValue ->
                    FieldRemarkValue

                Installment ->
                    FieldInstallment

                BatchNumber ->
                    FieldBatchNumber

                Passenger ->
                    FieldPassenger

                LegOfTheTrip ->
                    FieldLegOfTheTrip

                Probability ->
                    FieldProbability

                Suspicions ->
                    FieldSuspicions

                Empty ->
                    FieldEmpty
    in
        translate language translationId
