module Internationalization.Reimbursement.Fieldset exposing (..)

import Internationalization.Types exposing (TranslationSet)


currencyDetails : TranslationSet
currencyDetails =
    TranslationSet
        "Expense made abroad: "
        "Despesa feita no exterior "


detailsLink : TranslationSet
detailsLink =
    TranslationSet
        "check the currency rate on "
        "veja a cotação em "


companyDetails : TranslationSet
companyDetails =
    TranslationSet
        "If we can find the CNPJ of this supplier in our database more info will be available in the sidebar."
        "Se o CNPJ estiver no nosso banco de dados mais detalhes sobre o fornecedor aparecerão ao lado."


summary : TranslationSet
summary =
    TranslationSet
        "Summary"
        "Resumo"


reimbursement : TranslationSet
reimbursement =
    TranslationSet
        "Reimbursement details"
        "Detalhes do reembolso"


congressperson : TranslationSet
congressperson =
    TranslationSet
        "Congressperson details"
        "Detalhes do(a) deputado(a)"


congresspersonProfile : TranslationSet
congresspersonProfile =
    TranslationSet
        "Congressperson profile"
        "Perfil do(a) deputado(a)"


trip : TranslationSet
trip =
    TranslationSet
        "Ticket details"
        "Detalhes da passagem"
