module Reimbursement.Inputs.Update exposing (Msg(..), toQuery, update, updateFromQuery)

import Char
import Reimbursement.Fields as Fields exposing (Field(..), Label(..))
import Reimbursement.Inputs.Model exposing (Model)
import String
import List.Extra exposing (updateIf)


type Msg
    = Update String String


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


updateField : Model -> ( String, String ) -> Model
updateField model ( name, value ) =
    let
        fieldMatches field =
            Fields.getName field == name

        formatValue value =
            if Fields.isNumeric name then
                String.filter (\c -> Char.isDigit c || c == ' ') value
            else if name == "state" then
                String.map Char.toUpper value
            else if Fields.isDate name then
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
            query
                |> List.drop 1
                |> updateFromQuery (updateField model param)

        Nothing ->
            model


toQuery : Model -> List ( String, String )
toQuery model =
    model
        |> List.filter (Fields.getValue >> String.trim >> String.isEmpty >> not)
        |> List.map (\field -> ( Fields.getName field, Fields.getValue field |> String.trim ))
