module Documents.Inputs.Update exposing (Msg(..), toQuery, update, updateFromQuery, updateLanguage)

import Char
import Dict
import Documents.Fields as Fields
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import String
import Documents.Inputs.Model exposing (Model, Field)


type Msg
    = Update String String
    | Mdl (Material.Msg Msg)


formatDate : String -> String
formatDate value =
    let
        onlyDigits : String
        onlyDigits =
            String.filter (\c -> Char.isDigit c || c == ' ') value

        year : String
        year =
            onlyDigits
                |> String.left 4

        month : String
        month =
            onlyDigits
                |> String.dropLeft 4
                |> String.left 2

        day : String
        day =
            onlyDigits
                |> String.dropLeft 6
                |> String.left 2
    in
        [ year, month, day ]
            |> List.filter (\s -> not <| String.isEmpty s)
            |> String.join "-"


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Update name value ->
            ( updateField model ( name, value ), Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateField : Model -> ( String, String ) -> Model
updateField model ( name, value ) =
    case (Dict.get name model.inputs) of
        Just field ->
            let
                cleaned =
                    if Fields.isNumeric name then
                        String.filter (\c -> Char.isDigit c || c == ' ') value
                    else if name == "state" then
                        String.map Char.toUpper value
                    else if Fields.isDate name then
                        formatDate value
                    else
                        String.trim value

                inputs =
                    Dict.insert name { field | value = cleaned } model.inputs
            in
                { model | inputs = inputs }

        Nothing ->
            model


updateFromQuery : Model -> List ( String, String ) -> Model
updateFromQuery model queryList =
    let
        query =
            List.head queryList

        remaining =
            List.drop 1 queryList
    in
        case query of
            Just q ->
                updateFromQuery (updateField model q) remaining

            Nothing ->
                model


toQuery : Model -> List ( String, String )
toQuery model =
    model.inputs
        |> Dict.filter (\index field -> field.value |> String.trim |> String.isEmpty |> not)
        |> Dict.map (\index field -> String.trim field.value)
        |> Dict.toList


updateFieldLanguage : Language -> String -> Field -> Field
updateFieldLanguage lang key field =
    { field | label = Fields.getLabel lang key }


updateLanguage : Language -> Model -> Model
updateLanguage lang model =
    let
        inputs =
            Dict.map (updateFieldLanguage lang) model.inputs
    in
        { model | inputs = inputs, lang = lang }
