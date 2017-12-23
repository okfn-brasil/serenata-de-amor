module Internationalization.Reimbursement.Search exposing (..)

import Internationalization.Types exposing (TranslationSet)


fieldsetReimbursement : TranslationSet
fieldsetReimbursement =
    TranslationSet
        "Reimbursement data"
        "Dados do reembolso"


fieldsetCongressperson : TranslationSet
fieldsetCongressperson =
    TranslationSet
        "Congressperson & expense data"
        "Dados do(a) deputado(a) e da despesa"


search : TranslationSet
search =
    TranslationSet
        "Search"
        "Buscar"


newSearch : TranslationSet
newSearch =
    TranslationSet
        "New search"
        "Nova busca"


loading : TranslationSet
loading =
    TranslationSet
        "Loading…"
        "Carregando…"
