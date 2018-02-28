module Reimbursement.Search.Update exposing (Msg(..), toUrl, update, updateFromQuery)

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

        formattedValue =
            if Fields.isNumeric label then
                String.filter (\c -> Char.isDigit c || c == ' ') value
            else if label == State then
                String.map Char.toUpper value
            else if Fields.isDate label then
                formatDate value
            else
                String.trim value

        formatField (Field label value) =
            Field label formattedValue
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


{-| Convert a list of non-empty, searchable fields into a url:

    import Reimbursement.Fields exposing (Field(..), Label(..))

    toUrl [ Field Year "2016" ] --> "year/2016"

    toUrl [ Field Year "2016", Field Month "10" ] --> "year/2016/month/10"

    toUrl [ Field LegOfTheTrip "any" ] --> ""

    toUrl [ Field Year "" ] --> ""

-}
toUrl : Model -> String
toUrl model =
    model
        |> List.filterMap Fields.toQuery
        |> List.concatMap (\( label, value ) -> [ label, value ])
        |> String.join "/"
