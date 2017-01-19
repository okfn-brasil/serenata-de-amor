module Reimbursement.Search.Update exposing (Msg(..), toQuery, update, updateFromQuery)

import Char
import Reimbursement.Fields as Fields exposing (Field(..), Label(..))
import Reimbursement.Search.Model exposing (Model)
import String
import List.Extra exposing (updateIf)


type Msg
    = Update Label String


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
        Update label value ->
            ( updateField model label value, Cmd.none )


updateField : Model -> Label -> String -> Model
updateField model label value =
    let
        fieldMatches field =
            Fields.getLabel field == label

        formatValue value =
            if Fields.isNumeric label then
                String.filter (\c -> Char.isDigit c || c == ' ') value
            else if label == State then
                String.map Char.toUpper value
            else if Fields.isDate label then
                formatDate value
            else
                String.trim value

        formatField (Field label value) =
            Field label (formatValue value)
    in
        model
            |> updateIf fieldMatches formatField


updateFromQuery : Model -> List ( String, String ) -> Model
updateFromQuery model query =
    case List.head query of
        Just param ->
            let
                label =
                    (Fields.urlToLabel (Tuple.first param))

                value =
                    (Tuple.second param)
            in
                query
                    |> List.drop 1
                    |> updateFromQuery (updateField model label value)

        Nothing ->
            model


toQuery : Model -> List ( String, String )
toQuery model =
    model
        |> List.filter (Fields.getValue >> String.trim >> String.isEmpty >> not)
        |> List.map (\(Field label value) -> ( Fields.labelToUrl label, value |> String.trim ))
