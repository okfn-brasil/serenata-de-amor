module Internationalization exposing (Language(..), TranslationId(..), translate)


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
    | SearchFieldsetExpense
    | FieldsetCongressperson
    | FieldsetSubquota
    | FieldsetSupplier
    | FieldsetSupplierDetails
    | FieldsetDocument
    | FieldsetValues
    | FieldsetTrip
    | FieldsetApplication
    | FieldDocumentId
    | FieldCongresspersonName
    | FieldCongresspersonId
    | FieldCongresspersonDocument
    | FieldTerm
    | FieldState
    | FieldParty
    | FieldTermId
    | FieldSubquotaNumber
    | FieldSubquotaDescription
    | FieldSubquotaGroupId
    | FieldSubquotaGroupDescription
    | FieldSupplier
    | FieldCNPJOrCPF
    | FieldDocumentNumber
    | FieldDocumentType
    | FieldIssueDate
    | FieldDocumentValue
    | FieldRemarkValue
    | FieldNetValue
    | FieldMonth
    | FieldYear
    | FieldInstallment
    | FieldPassenger
    | FieldLegOfTheTrip
    | FieldBatchNumber
    | FieldReimbursementNumber
    | FieldReimbursementValue
    | FieldApplicantId
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
    | ResultTitleSingular
    | ResultTitlePlural
    | DocumentTitle
    | Search
    | NewSearch
    | Loading
    | PaginationPage
    | PaginationOf
    | DocumentNotFound


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
                        "Reimbursement"
                        "Reembolso"

                SearchFieldsetCongressperson ->
                    TranslationSet
                        "Congressperson"
                        "Deputado(a)"

                SearchFieldsetExpense ->
                    TranslationSet
                        "Expense"
                        "Despesa"

                FieldsetCongressperson ->
                    TranslationSet
                        "Congressperson"
                        "Deputado(a)"

                FieldsetSubquota ->
                    TranslationSet
                        "Subquota"
                        "Subquota"

                FieldsetSupplier ->
                    TranslationSet
                        "Supplier"
                        "Fornecedor"

                FieldsetSupplierDetails ->
                    TranslationSet
                        "If we can find the CNPJ of this supplier in our database more info will be available in the sidebar."
                        "Se o CNPJ estiver no nosso banco de dados mais detalhes sobre o fornecedor aparecerão ao lado."

                FieldsetDocument ->
                    TranslationSet
                        "Document"
                        "Documento"

                FieldsetValues ->
                    TranslationSet
                        "Values"
                        "Valores"

                FieldsetTrip ->
                    TranslationSet
                        "Trip"
                        "Viagens"

                FieldsetApplication ->
                    TranslationSet
                        "Application"
                        "Solicitante"

                FieldDocumentId ->
                    TranslationSet
                        "Document ID"
                        "ID do documento"

                FieldCongresspersonName ->
                    TranslationSet
                        "Congressperson name"
                        "Nome do parlamentar"

                FieldCongresspersonId ->
                    TranslationSet
                        "Congressperson ID"
                        "Cadastro do Parlamentar"

                FieldCongresspersonDocument ->
                    TranslationSet
                        "Congressperson document"
                        "Número da Carteira Parlamentar"

                FieldTerm ->
                    TranslationSet
                        "Term"
                        "Número da legislatura"

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

                FieldSubquotaNumber ->
                    TranslationSet
                        "Subquota number"
                        "Número da Subcota"

                FieldSubquotaDescription ->
                    TranslationSet
                        "Subquota description"
                        "Descrição da subquota"

                FieldSubquotaGroupId ->
                    TranslationSet
                        "Subquota group ID"
                        "Número da Especificação da Subcota"

                FieldSubquotaGroupDescription ->
                    TranslationSet
                        "Subquota group description"
                        "Descrição da Especificação da Subcota"

                FieldSupplier ->
                    TranslationSet
                        "Supplier"
                        "Fornecedor"

                FieldCNPJOrCPF ->
                    TranslationSet
                        "CNPJ or CPF"
                        "CNPJ ou CPF"

                FieldDocumentNumber ->
                    TranslationSet
                        "Document number"
                        "Número do documento"

                FieldDocumentType ->
                    TranslationSet
                        "Document type"
                        "Tipo do documento"

                FieldIssueDate ->
                    TranslationSet
                        "Issue date"
                        "Data de emissão"

                FieldDocumentValue ->
                    TranslationSet
                        "Document value"
                        "Valor do documento"

                FieldRemarkValue ->
                    TranslationSet
                        "Remark value"
                        "Valor da glosa"

                FieldNetValue ->
                    TranslationSet
                        "Net value"
                        "Valor líquido"

                FieldMonth ->
                    TranslationSet
                        "Month"
                        "Mês"

                FieldYear ->
                    TranslationSet
                        "Year"
                        "Ano"

                FieldInstallment ->
                    TranslationSet
                        "Installment"
                        "Número da parcela"

                FieldPassenger ->
                    TranslationSet
                        "Passenger"
                        "Passageiro"

                FieldLegOfTheTrip ->
                    TranslationSet
                        "Leg of the trip"
                        "Trecho"

                FieldBatchNumber ->
                    TranslationSet
                        "Batch number"
                        "Número do lote"

                FieldReimbursementNumber ->
                    TranslationSet
                        "Reimbursement number"
                        "Número do Ressarcimento"

                FieldReimbursementValue ->
                    TranslationSet
                        "Reimbursement value"
                        "Valor da Restituição"

                FieldApplicantId ->
                    TranslationSet
                        "Applicant ID"
                        "Identificador do Solicitante"

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
                        "SituationReason"
                        "Motivo situação"

                SupplierSituationDate ->
                    TranslationSet
                        "SituationDate"
                        "Data situação"

                SupplierSpecialSituation ->
                    TranslationSet
                        "SpecialSituation"
                        "Situação especial"

                SupplierSpecialSituationDate ->
                    TranslationSet
                        "SpecialSituationDate"
                        "Data situação especial"

                SupplierResponsibleFederativeEntity ->
                    TranslationSet
                        "ResponsibleFederativeEntity"
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
                        "AdditionalAddressDetails"
                        "Complemento"

                SupplierNeighborhood ->
                    TranslationSet
                        "Neighborhood"
                        "Bairro"

                SupplierZipCode ->
                    TranslationSet
                        "ZipCode"
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
                        "LastUpdated"
                        "Última atualização"

                SupplierMainActivity ->
                    TranslationSet
                        "MainActivity"
                        "Atividade principal"

                SupplierSecondaryActivity ->
                    TranslationSet
                        "SecondaryActivity"
                        "Atividades secundárias"

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
    in
        case lang of
            English ->
                translationSet.english

            Portuguese ->
                translationSet.portuguese
