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
    in
        case lang of
            English ->
                translationSet.english

            Portuguese ->
                translationSet.portuguese
