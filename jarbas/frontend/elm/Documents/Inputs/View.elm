module Documents.Inputs.View exposing (correctedFieldIndex, matchDate, view)

import Dict
import Documents.Fields as Fields
import Html exposing (br, p, span, text)
import Material
import Material.Grid exposing (grid, cell, size, Device(..))
import Material.Options as Options
import Material.Textfield as Textfield
import Material.Typography as Typography
import Documents.Inputs.Model exposing (Model, Field, model)
import Documents.Inputs.Update exposing (Msg(..), update)
import Internationalization exposing (TranslationId(..), translate)
import Regex


{-| Matches a date un the YYYY-MM-DD format

    >>> matchDate "1970-01-01"
    True

    >>> matchDate "foo-42-01"
    False

-}
matchDate : String -> Bool
matchDate value =
    if String.isEmpty value then
        True
    else
        let
            regex : Regex.Regex
            regex =
                Regex.regex
                    "[\\d]{4}-[\\d]{2}-[\\d]{2}"
        in
            value
                |> Regex.find Regex.All regex
                |> List.isEmpty
                |> not


getValue : Model -> String -> String
getValue model name =
    model.inputs
        |> Dict.get name
        |> Maybe.withDefault (Field "" "")
        |> .value


getField : Model -> String -> Field
getField model name =
    Maybe.withDefault
        (Field "" "")
        (Dict.get name model.inputs)


viewField : Model -> Bool -> ( Int, ( String, Field ) ) -> Html.Html Msg
viewField model loading ( index, ( name, field ) ) =
    let
        value =
            getValue model name

        base =
            [ Textfield.onInput (Update name)
            , Textfield.value field.value
            , Options.css "width" "100%"
            ]

        disabled =
            if loading then
                [ Textfield.disabled ]
            else
                []

        validationMsg =
            translate model.lang FieldIssueDateValidation

        dateValidation =
            if Fields.isDate name then
                [ Options.when (Textfield.error validationMsg) (not <| matchDate value) ]
            else
                []

        attrs =
            List.concat [ base, disabled, dateValidation ]
    in
        p []
            [ Options.styled span [ Typography.caption ] [ text field.label ]
            , br [] []
            , Textfield.render Mdl [ index ] model.mdl attrs
            ]


viewFieldset : Bool -> Model -> ( Int, ( String, List String ) ) -> Material.Grid.Cell Msg
viewFieldset loading model ( index, ( title, names ) ) =
    let
        fields =
            List.map (getField model) names

        namesAndFields =
            List.map2 (,) names fields

        indexedNamesAndFields =
            List.indexedMap (,) namesAndFields
                |> List.map (\( idx, field ) -> ( correctedFieldIndex index idx, field ))

        heading =
            [ Options.styled p [ Typography.title ] [ text title ] ]

        inputs =
            List.map (viewField model loading) indexedNamesAndFields
    in
        cell
            [ size Desktop 6, size Tablet 6, size Phone 6 ]
            (List.append heading inputs)


{-| Creates an unique index for each field, using the hundreds for the
filedset, and the units for the field itself:

    >>> correctedFieldIndex 0 42
    142

    >>> correctedFieldIndex 100 8
    10108

-}
correctedFieldIndex : Int -> Int -> Int
correctedFieldIndex fieldset field =
    ((fieldset + 1) * 100) + field


view : Bool -> Model -> Html.Html Msg
view loading model =
    grid [] <| List.map (viewFieldset loading model) (Fields.sets model.lang)
