module Internationalization.Reimbursement.Receipt exposing (..)

import Internationalization.Types exposing (TranslationSet)


notAvailable : TranslationSet
notAvailable =
    TranslationSet
        " Digitalized receipt not available."
        " Recibo não disponível."


available : TranslationSet
available =
    TranslationSet
        " View receipt"
        " Ver recibo"


fetch : TranslationSet
fetch =
    TranslationSet
        " Fetch receipt"
        " Buscar recibo"
