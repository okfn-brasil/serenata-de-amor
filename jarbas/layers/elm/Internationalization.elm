module Internationalization exposing (..)

import Internationalization.Common as Common
import Internationalization.DocumentType as DocumentType
import Internationalization.Reimbursement.Common as ReimbursementCommon
import Internationalization.Reimbursement.Company as ReimbursementCompany
import Internationalization.Reimbursement.Field as ReimbursementField
import Internationalization.Reimbursement.Fieldset as ReimbursementFieldset
import Internationalization.Reimbursement.Receipt as ReimbursementReceipt
import Internationalization.Reimbursement.Search as ReimbursementSearch
import Internationalization.Reimbursement.Tweet as ReimbursementTweet
import Internationalization.Suspicion as Suspicion
import Internationalization.Types exposing (Language(..), TranslationId(..), TranslationSet)


translate : Language -> TranslationId -> String
translate lang trans =
    let
        translationSet =
            case trans of
                About ->
                    Common.about

                AboutJarbas ->
                    Common.aboutJarbas

                AboutSerenata ->
                    Common.aboutSerenata

                AboutDatasets ->
                    Common.aboutDatasets

                SearchFieldsetReimbursement ->
                    ReimbursementSearch.fieldsetReimbursement

                SearchFieldsetCongressperson ->
                    ReimbursementSearch.fieldsetCongressperson

                FieldsetSummary ->
                    ReimbursementFieldset.summary

                FieldsetTrip ->
                    ReimbursementFieldset.trip

                FieldsetCongressperson ->
                    ReimbursementFieldset.congressperson

                FieldsetReimbursement ->
                    ReimbursementFieldset.reimbursement

                FieldsetCompanyDetails ->
                    ReimbursementFieldset.companyDetails

                FieldsetCongresspersonProfile ->
                    ReimbursementFieldset.congresspersonProfile

                FieldsetCurrencyDetails ->
                    ReimbursementFieldset.currencyDetails

                FieldsetCurrencyDetailsLink ->
                    ReimbursementFieldset.detailsLink

                FieldYear ->
                    ReimbursementField.year

                FieldDocumentId ->
                    ReimbursementField.documentId

                FieldApplicantId ->
                    ReimbursementField.applicantId

                FieldTotalReimbursementValue ->
                    ReimbursementField.totalReimbursementValue

                FieldTotalNetValue ->
                    ReimbursementField.totalNetValue

                FieldReimbursementNumbers ->
                    ReimbursementField.reimbursementNumbers

                FieldNetValues ->
                    ReimbursementField.netValues

                FieldCongresspersonId ->
                    ReimbursementField.congresspersonId

                FieldCongressperson ->
                    ReimbursementField.congressperson

                FieldCongresspersonName ->
                    ReimbursementField.congresspersonName

                FieldCongresspersonDocument ->
                    ReimbursementField.congresspersonDocument

                FieldState ->
                    ReimbursementField.state

                FieldParty ->
                    ReimbursementField.party

                FieldTermId ->
                    ReimbursementField.termId

                FieldTerm ->
                    ReimbursementField.term

                FieldSubquotaId ->
                    ReimbursementField.subquotaId

                FieldSubquotaDescription ->
                    ReimbursementField.subquotaDescription

                FieldSubquotaGroupId ->
                    ReimbursementField.subquotaGroupId

                FieldSubquotaGroupDescription ->
                    ReimbursementField.subquotaGroupDescription

                FieldCompany ->
                    ReimbursementField.company

                FieldCnpjCpf ->
                    ReimbursementField.cnpjCpf

                FieldDocumentType ->
                    ReimbursementField.documentType

                FieldDocumentNumber ->
                    ReimbursementField.documentNumber

                FieldDocumentValue ->
                    ReimbursementField.documentValue

                FieldIssueDate ->
                    ReimbursementField.issueDate

                FieldIssueDateStart ->
                    ReimbursementField.issueDateStart

                FieldIssueDateEnd ->
                    ReimbursementField.issueDateEnd

                FieldIssueDateValidation ->
                    ReimbursementField.issueDateValidation

                FieldClaimDate ->
                    ReimbursementField.claimDate

                FieldMonth ->
                    ReimbursementField.month

                FieldRemarkValue ->
                    ReimbursementField.remarkValue

                FieldInstallment ->
                    ReimbursementField.installment

                FieldBatchNumber ->
                    ReimbursementField.batchNumber

                FieldReimbursementValues ->
                    ReimbursementField.reimbursementValues

                FieldPassenger ->
                    ReimbursementField.passenger

                FieldLegOfTheTrip ->
                    ReimbursementField.legOfTheTrip

                FieldProbability ->
                    ReimbursementField.probability

                FieldSuspicions ->
                    ReimbursementField.suspicions

                FieldEmpty ->
                    Common.empty

                ReimbursementSource ->
                    ReimbursementCommon.reimbursementSource

                ReimbursementDeletedSource ->
                    ReimbursementCommon.reimbursementDeletedSource

                ReimbursementChamberOfDeputies ->
                    ReimbursementCommon.reimbursementChamberOfDeputies

                ReceiptFetch ->
                    ReimbursementReceipt.fetch

                ReceiptAvailable ->
                    ReimbursementReceipt.available

                ReceiptNotAvailable ->
                    ReimbursementReceipt.notAvailable

                Map ->
                    ReimbursementCommon.map

                CompanyCNPJ ->
                    ReimbursementCompany.cnpj

                CompanyTradeName ->
                    ReimbursementCompany.tradeName

                CompanyName ->
                    ReimbursementCompany.name

                CompanyOpeningDate ->
                    ReimbursementCompany.openingDate

                CompanyLegalEntity ->
                    ReimbursementCompany.legalEntity

                CompanyType ->
                    ReimbursementCompany.companyType

                CompanyStatus ->
                    ReimbursementCompany.status

                CompanySituation ->
                    ReimbursementCompany.situation

                CompanySituationReason ->
                    ReimbursementCompany.situationReason

                CompanySituationDate ->
                    ReimbursementCompany.situationDate

                CompanySpecialSituation ->
                    ReimbursementCompany.specialSituation

                CompanySpecialSituationDate ->
                    ReimbursementCompany.specialSituationDate

                CompanyResponsibleFederativeEntity ->
                    ReimbursementCompany.responsibleFederativeEntity

                CompanyAddress ->
                    ReimbursementCompany.address

                CompanyNumber ->
                    ReimbursementCompany.number

                CompanyAdditionalAddressDetails ->
                    ReimbursementCompany.additionalAddressDetails

                CompanyNeighborhood ->
                    ReimbursementCompany.neighborhood

                CompanyZipCode ->
                    ReimbursementCompany.zipCode

                CompanyCity ->
                    ReimbursementCompany.city

                CompanyState ->
                    ReimbursementCompany.state

                CompanyEmail ->
                    ReimbursementCompany.email

                CompanyPhone ->
                    ReimbursementCompany.phone

                CompanyLastUpdated ->
                    ReimbursementCompany.lastUpdated

                CompanyMainActivity ->
                    ReimbursementCompany.mainActivity

                CompanySecondaryActivity ->
                    ReimbursementCompany.secondaryActivity

                CompanySource ->
                    ReimbursementCompany.source

                CompanyFederalRevenue ->
                    ReimbursementCompany.federalRevenue

                ReimbursementTitle ->
                    ReimbursementCommon.reimbursementTitle

                ReimbursementDeletedTitle ->
                    ReimbursementCommon.reimbursementDeletedTitle

                ResultTitleSingular ->
                    ReimbursementCommon.resultTitleSingular

                ResultTitlePlural ->
                    ReimbursementCommon.resultTitlePlural

                Search ->
                    ReimbursementSearch.search

                NewSearch ->
                    ReimbursementSearch.newSearch

                Loading ->
                    ReimbursementSearch.loading

                RosiesTweet ->
                    ReimbursementTweet.rosiesTweet

                PaginationPage ->
                    ReimbursementCommon.paginationPage

                PaginationOf ->
                    ReimbursementCommon.paginationOf

                ReimbursementNotFound ->
                    ReimbursementCommon.reimbursementNotFound

                SameDayTitle ->
                    ReimbursementCommon.sameDayTitle

                SameSubquotaTitle ->
                    ReimbursementCommon.sameSubquoteTitle

                BrazilianCurrency value ->
                    Common.brazilianCurrency value

                ThousandSeparator ->
                    Common.thousandSeparator

                DecimalSeparator ->
                    Common.decimalSeparator

                Suspicion suspicion ->
                    case suspicion of
                        "meal_price_outlier" ->
                            Suspicion.mealPriceOutlier

                        "over_monthly_subquota_limit" ->
                            Suspicion.overMonthlySubquoteLimit

                        "suspicious_traveled_speed_day" ->
                            Suspicion.suspiciousTraveledSpeedDay

                        "invalid_cnpj_cpf" ->
                            Suspicion.invalidCpfCnpj

                        "election_expenses" ->
                            Suspicion.electionExpenses

                        "irregular_companies_classifier" ->
                            Suspicion.irregularCompany

                        _ ->
                            TranslationSet
                                suspicion
                                suspicion

                DocumentType value ->
                    case value of
                        0 ->
                            DocumentType.billOfSale

                        1 ->
                            DocumentType.simpleReceipt

                        2 ->
                            DocumentType.expenseMadeAbroad

                        _ ->
                            Common.empty
    in
        case lang of
            English ->
                translationSet.english

            Portuguese ->
                translationSet.portuguese
