module Internationalization exposing (Language(..), TranslationId(..), translate)

import Date
import Date.Format


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
    | FieldsetSupplierDetails
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
    | FieldSupplier
    | FieldCnpjCpf
    | FieldDocumentType
    | FieldDocumentNumber
    | FieldDocumentValue
    | FieldIssueDate
    | FieldMonth
    | FieldClaimDate
    | FieldRemarkValue
    | FieldInstallment
    | FieldBatchNumber
    | FieldReimbursementValues
    | FieldPassenger
    | FieldLegOfTheTrip
    | FieldProbability
    | FieldSuspicions
    | DocumentSource
    | DocumentChamberOfDeputies
    | ReceiptFetch
    | ReceiptAvailable
    | ReceiptNotAvailable
    | Map
    | SupplierCNPJ
    | SupplierTradeName
    | SupplierName
    | SupplierOpeningDate
    | SupplierLegalEntity
    | SupplierType
    | SupplierStatus
    | SupplierSituation
    | SupplierSituationReason
    | SupplierSituationDate
    | SupplierSpecialSituation
    | SupplierSpecialSituationDate
    | SupplierResponsibleFederativeEntity
    | SupplierAddress
    | SupplierNumber
    | SupplierAdditionalAddressDetails
    | SupplierNeighborhood
    | SupplierZipCode
    | SupplierCity
    | SupplierState
    | SupplierEmail
    | SupplierPhone
    | SupplierLastUpdated
    | SupplierMainActivity
    | SupplierSecondaryActivity
    | SupplierSource
    | SupplierFederalRevenue
    | ResultTitleSingular
    | ResultTitlePlural
    | DocumentTitle
    | Search
    | NewSearch
    | Loading
    | PaginationPage
    | PaginationOf
    | DocumentNotFound
    | BrazilianCurrency String
    | ThousandSeparator
    | DecimalSeparator
    | FormattedDate Date.Date
    | Suspicion String
    | DocumentType Int


translate : Language -> TranslationId -> String
translate lang trans =
    let
        translationSet =
            case trans of
                About ->
                    TranslationSet
                        "About"
                        "Sobre"

                AboutJarbas ->
                    TranslationSet
                        "About Jarbas"
                        "Sobre o Jarbas"

                AboutSerenata ->
                    TranslationSet
                        "About Serenata de Amor"
                        "Sobre a Serenata de Amor"

                AboutDatasets ->
                    TranslationSet
                        "About the dataset"
                        "Sobre a base de dados"

                SearchFieldsetReimbursement ->
                    TranslationSet
                        "Reimbursement data"
                        "Dados do reembolso"

                SearchFieldsetCongressperson ->
                    TranslationSet
                        "Congressperson & expense data"
                        "Dados do(a) deputado(a) e da despesa"

                FieldsetSummary ->
                    TranslationSet
                        "Summary"
                        "Resumo"

                FieldsetTrip ->
                    TranslationSet
                        "Ticket details"
                        "Detalhes da passagem"

                FieldsetCongressperson ->
                    TranslationSet
                        "Congressperson details"
                        "Detalhes do(a) deputado(a)"

                FieldsetReimbursement ->
                    TranslationSet
                        "Reimbursement details"
                        "Detalhes do reembolso"

                FieldsetSupplierDetails ->
                    TranslationSet
                        "If we can find the CNPJ of this supplier in our database more info will be available in the sidebar."
                        "Se o CNPJ estiver no nosso banco de dados mais detalhes sobre o fornecedor aparecerão ao lado."

                FieldsetCurrencyDetails ->
                    TranslationSet
                        "Expense made abroad: "
                        "Despesa feita no exterior "

                FieldsetCurrencyDetailsLink ->
                    TranslationSet
                        "check the currency rate on "
                        "veja a cotação em "

                FieldYear ->
                    TranslationSet
                        "Year"
                        "Ano"

                FieldDocumentId ->
                    TranslationSet
                        "Document ID"
                        "ID do documento"

                FieldApplicantId ->
                    TranslationSet
                        "Applicant ID"
                        "Identificador do Solicitante"

                FieldTotalReimbursementValue ->
                    TranslationSet
                        "Total reimbursement value"
                        "Valor total dos reembolsos"

                FieldTotalNetValue ->
                    TranslationSet
                        "Total net value"
                        "Valor líquido total"

                FieldReimbursementNumbers ->
                    TranslationSet
                        "Reimbursement number"
                        "Número dos reembolsos"

                FieldNetValues ->
                    TranslationSet
                        "Net values"
                        "Valores líquidos"

                FieldCongresspersonId ->
                    TranslationSet
                        "Congressperson ID"
                        "Cadastro do Parlamentar"

                FieldCongressperson ->
                    TranslationSet
                        "Congressperson"
                        "Deputado(a)"

                FieldCongresspersonName ->
                    TranslationSet
                        "Congressperson nome"
                        "Nome do(a) deputado(a)"

                FieldCongresspersonDocument ->
                    TranslationSet
                        "Congressperson document"
                        "Número da Carteira Parlamentar"

                FieldState ->
                    TranslationSet
                        "State"
                        "UF"

                FieldParty ->
                    TranslationSet
                        "Party"
                        "Partido"

                FieldTermId ->
                    TranslationSet
                        "Term ID"
                        "Código da legislatura"

                FieldTerm ->
                    TranslationSet
                        "Term"
                        "Número da legislatura"

                FieldSubquotaId ->
                    TranslationSet
                        "Subquota number"
                        "Número da Subcota"

                FieldSubquotaDescription ->
                    TranslationSet
                        "Subquota"
                        "Subquota"

                FieldSubquotaGroupId ->
                    TranslationSet
                        "Subquota group number"
                        "Número da especificação da subcota"

                FieldSubquotaGroupDescription ->
                    TranslationSet
                        "Subquota group"
                        "Especificação da subcota"

                FieldSupplier ->
                    TranslationSet
                        "Supplier"
                        "Fornecedor"

                FieldCnpjCpf ->
                    TranslationSet
                        "CNPJ or CPF"
                        "CNPJ ou CPF"

                FieldDocumentType ->
                    TranslationSet
                        "Document type"
                        "Tipo do documento"

                FieldDocumentNumber ->
                    TranslationSet
                        "Document number"
                        "Número do documento"

                FieldDocumentValue ->
                    TranslationSet
                        "Expense value"
                        "Valor da despesa"

                FieldIssueDate ->
                    TranslationSet
                        "Expense date"
                        "Data da despesa"

                FieldClaimDate ->
                    TranslationSet
                        "Claim date"
                        "Data do pedido de reembolso"

                FieldMonth ->
                    TranslationSet
                        "Month"
                        "Mês"

                FieldRemarkValue ->
                    TranslationSet
                        "Remark value"
                        "Valor da glosa"

                FieldInstallment ->
                    TranslationSet
                        "Installment"
                        "Número da parcela"

                FieldBatchNumber ->
                    TranslationSet
                        "Batch number"
                        "Número do lote"

                FieldReimbursementValues ->
                    TranslationSet
                        "Reimbursement values"
                        "Valor dos reembolsos"

                FieldPassenger ->
                    TranslationSet
                        "Passenger"
                        "Passageiro"

                FieldLegOfTheTrip ->
                    TranslationSet
                        "Leg of the trip"
                        "Trecho"

                FieldProbability ->
                    TranslationSet
                        "Probability"
                        "Probabilidade"

                FieldSuspicions ->
                    TranslationSet
                        "Suspicions"
                        "Suspeitas"

                DocumentSource ->
                    TranslationSet
                        "Source: "
                        "Fonte: "

                DocumentChamberOfDeputies ->
                    TranslationSet
                        "Chamber of Deputies"
                        "Câmara dos Deputados"

                ReceiptFetch ->
                    TranslationSet
                        " Fetch receipt"
                        " Buscar recibo"

                ReceiptAvailable ->
                    TranslationSet
                        " View receipt"
                        " Ver recibo"

                ReceiptNotAvailable ->
                    TranslationSet
                        " Digitalized receipt not available."
                        " Recibo não disponível."

                Map ->
                    TranslationSet
                        " Supplier on Maps"
                        " Ver no Google Maps"

                SupplierCNPJ ->
                    TranslationSet
                        "CNPJ"
                        "CNPJ"

                SupplierTradeName ->
                    TranslationSet
                        "Trade name"
                        "Nome fantasia"

                SupplierName ->
                    TranslationSet
                        "Name"
                        "Razão social"

                SupplierOpeningDate ->
                    TranslationSet
                        "Opening date"
                        "Data de abertura"

                SupplierLegalEntity ->
                    TranslationSet
                        "Legal entity"
                        "Natureza jurídica"

                SupplierType ->
                    TranslationSet
                        "Type"
                        "Tipo"

                SupplierStatus ->
                    TranslationSet
                        "Status"
                        "Status"

                SupplierSituation ->
                    TranslationSet
                        "Situation"
                        "Situação"

                SupplierSituationReason ->
                    TranslationSet
                        "Situation Reason"
                        "Motivo situação"

                SupplierSituationDate ->
                    TranslationSet
                        "Situation Date"
                        "Data situação"

                SupplierSpecialSituation ->
                    TranslationSet
                        "Special Situation"
                        "Situação especial"

                SupplierSpecialSituationDate ->
                    TranslationSet
                        "Special Situation Date"
                        "Data situação especial"

                SupplierResponsibleFederativeEntity ->
                    TranslationSet
                        "Responsible Federative Entity"
                        "EFR"

                SupplierAddress ->
                    TranslationSet
                        "Address"
                        "Endereço"

                SupplierNumber ->
                    TranslationSet
                        "Number"
                        "Número"

                SupplierAdditionalAddressDetails ->
                    TranslationSet
                        "Additional Address Details"
                        "Complemento"

                SupplierNeighborhood ->
                    TranslationSet
                        "Neighborhood"
                        "Bairro"

                SupplierZipCode ->
                    TranslationSet
                        "Zip Code"
                        "CEP"

                SupplierCity ->
                    TranslationSet
                        "City"
                        "Cidade"

                SupplierState ->
                    TranslationSet
                        "State"
                        "Estado"

                SupplierEmail ->
                    TranslationSet
                        "Email"
                        "Email"

                SupplierPhone ->
                    TranslationSet
                        "Telephone"
                        "Telefone"

                SupplierLastUpdated ->
                    TranslationSet
                        "Last Updated"
                        "Última atualização"

                SupplierMainActivity ->
                    TranslationSet
                        "Main Activity"
                        "Atividade principal"

                SupplierSecondaryActivity ->
                    TranslationSet
                        "Secondary Activity"
                        "Atividades secundárias"

                SupplierSource ->
                    TranslationSet
                        "Source: "
                        "Fonte: "

                SupplierFederalRevenue ->
                    TranslationSet
                        "Federal Revenue of Brazil"
                        "Receita Federal"

                DocumentTitle ->
                    TranslationSet
                        "Document #"
                        "Documento nº"

                ResultTitleSingular ->
                    TranslationSet
                        " document found."
                        " documento encontrado."

                ResultTitlePlural ->
                    TranslationSet
                        " documents found."
                        " documentos encontrados."

                Search ->
                    TranslationSet
                        "Search"
                        "Buscar"

                NewSearch ->
                    TranslationSet
                        "New search"
                        "Nova busca"

                Loading ->
                    TranslationSet
                        "Loading…"
                        "Carregando…"

                PaginationPage ->
                    TranslationSet
                        "Page "
                        "Página "

                PaginationOf ->
                    TranslationSet
                        " of "
                        " de "

                DocumentNotFound ->
                    TranslationSet
                        "Document not found."
                        "Documento não encontrado."

                BrazilianCurrency value ->
                    TranslationSet
                        (value ++ " BRL")
                        ("R$ " ++ value)

                ThousandSeparator ->
                    TranslationSet
                        ","
                        "."

                DecimalSeparator ->
                    TranslationSet
                        "."
                        ","

                FormattedDate date ->
                    TranslationSet
                        (Date.Format.format "%b %e, %Y" date)
                        (Date.Format.format "%d/%m/%Y" date)

                Suspicion suspicion ->
                    case suspicion of
                        "meal_price_outlier" ->
                            TranslationSet
                                "Meal price is an outlier"
                                "Preço de refeição muito incomum"

                        "over_monthly_subquota_limit" ->
                            TranslationSet
                                "Expenses over the (sub)quota limit"
                                "Extrapolou limita da (sub)quota"

                        "suspicious_traveled_speed_day" ->
                            TranslationSet
                                "Many expenses in different cities at the same day"
                                "Muitas despesas em diferentes cidades no mesmo dia"

                        _ ->
                            TranslationSet
                                suspicion
                                suspicion

                DocumentType value ->
                    case value of
                        0 ->
                            TranslationSet
                                "Bill of sale"
                                "Nota fiscal"

                        1 ->
                            TranslationSet
                                "Simple receipt"
                                "Recibo simples"

                        2 ->
                            TranslationSet
                                "Expesne made abroad"
                                "Despesa no exterior"

                        _ ->
                            TranslationSet
                                ""
                                ""
    in
        case lang of
            English ->
                translationSet.english

            Portuguese ->
                translationSet.portuguese
