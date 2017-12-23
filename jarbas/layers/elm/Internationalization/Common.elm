module Internationalization.Common exposing (..)

import Internationalization.Types exposing (TranslationSet)


about : TranslationSet
about =
    TranslationSet
        "About"
        "Sobre"


aboutJarbas : TranslationSet
aboutJarbas =
    TranslationSet
        "About Jarbas"
        "Sobre o Jarbas"


aboutDatasets : TranslationSet
aboutDatasets =
    TranslationSet
        "About the dataset"
        "Sobre a base de dados"


aboutSerenata : TranslationSet
aboutSerenata =
    TranslationSet
        "About Serenata de Amor"
        "Sobre a Serenata de Amor"


thousandSeparator : TranslationSet
thousandSeparator =
    TranslationSet
        ","
        "."


decimalSeparator : TranslationSet
decimalSeparator =
    TranslationSet
        "."
        ","


brazilianCurrency : String -> TranslationSet
brazilianCurrency value =
    TranslationSet
        (value ++ " BRL")
        ("R$ " ++ value)


empty : TranslationSet
empty =
    TranslationSet
        ""
        ""
