module Reimbursement.Fields exposing (..)

import Internationalization exposing (Language(..), TranslationId(..), TranslationSet, translateSet)
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
    | Congressperson
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
    | ClaimDate
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
    [ ( ApplicantId, "applicantId" )
    , ( CnpjCpf, "cnpjCpf" )
    , ( DocumentId, "documentId" )
    , ( IssueDateEnd, "issueDateEnd" )
    , ( IssueDateStart, "issueDateStart" )
    , ( Month, "month" )
    , ( SubquotaId, "subquotaId" )
    , ( Year, "year" )
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
        translationSet =
            case label of
                Year ->
                    TranslationSet "Year"
                        "Ano"

                DocumentId ->
                    TranslationSet "Document ID"
                        "ID do documento"

                ApplicantId ->
                    TranslationSet "Applicant ID"
                        "Identificador do Solicitante"

                TotalReimbursementValue ->
                    TranslationSet "Total reimbursement value"
                        "Valor total dos reembolsos"

                TotalNetValue ->
                    TranslationSet "Total net value"
                        "Valor líquido total"

                ReimbursementNumbers ->
                    TranslationSet "Reimbursement number"
                        "Número dos reembolsos"

                NetValues ->
                    TranslationSet "Net values"
                        "Valores líquidos"

                CongresspersonId ->
                    TranslationSet "Congressperson ID"
                        "Cadastro do Parlamentar"

                Congressperson ->
                    TranslationSet "Congressperson"
                        "Deputado(a)"

                CongresspersonName ->
                    TranslationSet "Congressperson nome"
                        "Nome do(a) deputado(a)"

                CongresspersonDocument ->
                    TranslationSet "Congressperson document"
                        "Número da Carteira Parlamentar"

                State ->
                    TranslationSet "State"
                        "UF"

                Party ->
                    TranslationSet "Party"
                        "Partido"

                TermId ->
                    TranslationSet "Term ID"
                        "Código da legislatura"

                Term ->
                    TranslationSet "Term"
                        "Número da legislatura"

                SubquotaId ->
                    TranslationSet "Subquota number"
                        "Número da Subcota"

                SubquotaDescription ->
                    TranslationSet "Subquota"
                        "Subquota"

                SubquotaGroupId ->
                    TranslationSet "Subquota group number"
                        "Número da especificação da subcota"

                SubquotaGroupDescription ->
                    TranslationSet "Subquota group"
                        "Especificação da subcota"

                Company ->
                    TranslationSet "Company"
                        "Fornecedor"

                CnpjCpf ->
                    TranslationSet "CNPJ or CPF"
                        "CNPJ ou CPF"

                DocumentType ->
                    TranslationSet "Document type"
                        "Tipo do documento"

                DocumentNumber ->
                    TranslationSet "Document number"
                        "Número do documento"

                DocumentValue ->
                    TranslationSet "Expense value"
                        "Valor da despesa"

                IssueDate ->
                    TranslationSet "Expense date"
                        "Data da despesa"

                IssueDateStart ->
                    TranslationSet "Expense date (start)"
                        "Data da despesa (início)"

                IssueDateEnd ->
                    TranslationSet "Expense date (end)"
                        "Data da despesa (fim)"

                ClaimDate ->
                    TranslationSet "Claim date"
                        "Data do pedido de reembolso"

                Month ->
                    TranslationSet "Month"
                        "Mês"

                RemarkValue ->
                    TranslationSet "Remark value"
                        "Valor da glosa"

                Installment ->
                    TranslationSet "Installment"
                        "Número da parcela"

                BatchNumber ->
                    TranslationSet "Batch number"
                        "Número do lote"

                ReimbursementValues ->
                    TranslationSet "Reimbursement values"
                        "Valor dos reembolsos"

                Passenger ->
                    TranslationSet "Passenger"
                        "Passageiro"

                LegOfTheTrip ->
                    TranslationSet "Leg of the trip"
                        "Trecho"

                Probability ->
                    TranslationSet "Probability"
                        "Probabilidade"

                Suspicions ->
                    TranslationSet "Suspicions"
                        "Suspeitas"

                Empty ->
                    TranslationSet "" ""
    in
        translateSet language translationSet
