module Reimbursement.Search.View exposing (correctedFieldIndex, matchDate, view)

import Html exposing (br, p, span, text)
import Internationalization exposing (TranslationId(..), Language, translate)
import Material.Grid exposing (Device(..), cell, grid, size)
import Material.Options as Options
import Material.Textfield as Textfield
import Material.Typography as Typography
import Regex
import Reimbursement.Fields as Fields exposing (Field(..), Label(..))
import Reimbursement.Search.Update exposing (Msg(..), update)
import Reimbursement.Update as RootMsg exposing (Msg(..))
import Reimbursement.Model as RootModel exposing (Model)
import List.Extra


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
                Regex.regex "[\\d]{4}-[\\d]{2}-[\\d]{2}"
        in
            value
                |> Regex.find Regex.All regex
                |> List.isEmpty
                |> not


getField : RootModel.Model -> String -> Field
getField model name =
    List.Extra.find (Fields.getName >> (==) name) model.searchFields
        |> Maybe.withDefault (Field (Label EmptyField "") "")


viewField : RootModel.Model -> ( Int, ( String, Field ) ) -> Html.Html RootMsg.Msg
viewField model ( index, ( name, field ) ) =
    let
        value =
            Fields.getValue field

        base =
            [ Textfield.onInput (Update name >> RootMsg.SearchMsg)
            , Textfield.value value
            , Options.css "width" "100%"
            ]

        disabled =
            if model.loading then
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
            [ Options.styled span [ Typography.caption ] [ text <| Fields.getLabelTranslation model.lang field ]
            , br [] []
            , Textfield.render RootMsg.Mdl [ index ] model.mdl attrs
            ]


viewFieldset : RootModel.Model -> ( Int, ( TranslationId, List String ) ) -> Material.Grid.Cell RootMsg.Msg
viewFieldset model ( index, ( title, names ) ) =
    let
        fields =
            List.map (getField model) names

        namesAndFields =
            List.map2 (,) names fields

        indexedNamesAndFields =
            List.indexedMap (,) namesAndFields
                |> List.map (\( idx, field ) -> ( correctedFieldIndex index idx, field ))

        heading =
            [ Options.styled p [ Typography.title ] [ text <| translate model.lang title ] ]

        searchFields =
            List.map (viewField model) indexedNamesAndFields
    in
        cell [ size Desktop 6, size Tablet 6, size Phone 6 ]
            (List.append heading searchFields)


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


view : RootModel.Model -> Html.Html RootMsg.Msg
view model =
    grid [] <| List.map (viewFieldset model) Fields.sets
