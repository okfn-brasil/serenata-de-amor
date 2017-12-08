module Internationalization.Reimbursement.Common exposing (..)

import Internationalization.Types exposing (TranslationSet)


paginationPage : TranslationSet
paginationPage =
    TranslationSet
        "Page "
        "Página "


paginationOf : TranslationSet
paginationOf =
    TranslationSet
        " of "
        " de "


reimbursementNotFound : TranslationSet
reimbursementNotFound =
    TranslationSet
        "Document not found."
        "Documento não encontrado."


reimbursementTitle : TranslationSet
reimbursementTitle =
    TranslationSet
        "Document #"
        "Documento nº"


reimbursementDeletedTitle : TranslationSet
reimbursementDeletedTitle =
    TranslationSet
        "Reimbursement deleted from the source"
        "Reembolso excluído na base de dados da Câmara"


reimbursementSource : TranslationSet
reimbursementSource =
    TranslationSet
        "Source: "
        "Fonte: "


reimbursementDeletedSource : TranslationSet
reimbursementDeletedSource =
    TranslationSet
        " (the source might not be available anymore since the reimbursement was not present in the last version of their dataset)"
        " (a fonte pode não estar mais disponível já que o reembolso não constava na última versão dos dados divulgados por eles)"


reimbursementChamberOfDeputies : TranslationSet
reimbursementChamberOfDeputies =
    TranslationSet
        "Chamber of Deputies"
        "Câmara dos Deputados"


resultTitleSingular : TranslationSet
resultTitleSingular =
    TranslationSet
        " document found."
        " documento encontrado."


resultTitlePlural : TranslationSet
resultTitlePlural =
    TranslationSet
        " documents found."
        " documentos encontrados."


map : TranslationSet
map =
    TranslationSet
        " Company on Maps"
        " Ver no Google Maps"


sameSubquoteTitle : TranslationSet
sameSubquoteTitle =
    TranslationSet
        "Other reimbursements from the same month & subquota"
        "Outros reembolsos do mesmo mês e subquota"


sameDayTitle : TranslationSet
sameDayTitle =
    TranslationSet
        "Other reimbursements from the same day"
        "Outros reembolsos do mesmo dia"
