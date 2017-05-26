module Internationalization.Types exposing (..)


type alias TranslationSet =
    { english : String
    , portuguese : String
    }


type Language
    = English
    | Portuguese


type TranslationId
    = About
    | AboutJarbas
    | AboutSerenata
    | AboutDatasets
    | SearchFieldsetReimbursement
    | SearchFieldsetCongressperson
    | FieldsetSummary
    | FieldsetTrip
    | FieldsetReimbursement
    | FieldsetCongressperson
    | FieldsetCompanyDetails
    | FieldsetCurrencyDetails
    | FieldsetCurrencyDetailsLink
    | FieldYear
    | FieldDocumentId
    | FieldApplicantId
    | FieldTotalReimbursementValue
    | FieldTotalNetValue
    | FieldReimbursementNumbers
    | FieldNetValues
    | FieldCongresspersonId
    | FieldCongressperson
    | FieldCongresspersonName
    | FieldCongresspersonDocument
    | FieldState
    | FieldParty
    | FieldTermId
    | FieldTerm
    | FieldSubquotaId
    | FieldSubquotaDescription
    | FieldSubquotaGroupId
    | FieldSubquotaGroupDescription
    | FieldCompany
    | FieldCnpjCpf
    | FieldDocumentType
    | FieldDocumentNumber
    | FieldDocumentValue
    | FieldIssueDate
    | FieldIssueDateStart
    | FieldIssueDateEnd
    | FieldIssueDateValidation
    | FieldClaimDate
    | FieldMonth
    | FieldRemarkValue
    | FieldInstallment
    | FieldBatchNumber
    | FieldReimbursementValues
    | FieldPassenger
    | FieldLegOfTheTrip
    | FieldProbability
    | FieldSuspicions
    | FieldEmpty
    | ReimbursementSource
    | ReimbursementChamberOfDeputies
    | ReceiptFetch
    | ReceiptAvailable
    | ReceiptNotAvailable
    | Map
    | CompanyCNPJ
    | CompanyTradeName
    | CompanyName
    | CompanyOpeningDate
    | CompanyLegalEntity
    | CompanyType
    | CompanyStatus
    | CompanySituation
    | CompanySituationReason
    | CompanySituationDate
    | CompanySpecialSituation
    | CompanySpecialSituationDate
    | CompanyResponsibleFederativeEntity
    | CompanyAddress
    | CompanyNumber
    | CompanyAdditionalAddressDetails
    | CompanyNeighborhood
    | CompanyZipCode
    | CompanyCity
    | CompanyState
    | CompanyEmail
    | CompanyPhone
    | CompanyLastUpdated
    | CompanyMainActivity
    | CompanySecondaryActivity
    | CompanySource
    | CompanyFederalRevenue
    | ResultTitleSingular
    | ResultTitlePlural
    | ReimbursementTitle
    | ReimbursementDeletedTitle
    | Search
    | NewSearch
    | Loading
    | PaginationPage
    | PaginationOf
    | ReimbursementNotFound
    | SameDayTitle
    | SameSubquotaTitle
    | BrazilianCurrency String
    | ThousandSeparator
    | DecimalSeparator
    | Suspicion String
    | DocumentType Int
