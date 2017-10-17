module Reimbursement.Search.View exposing (correctedFieldIndex, matchDate, view)

import Html exposing (Html, br, p, span, text, form, div)
import Html.Events exposing (onSubmit)
import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..))
import List.Extra
import Material.Button as Button
import Material.Grid exposing (Device(..), cell, grid, size)
import Material.Options as Options
import Material.Textfield as Textfield
import Material.Typography as Typography
import Regex
import Reimbursement.Fields as Fields exposing (Field(..), Label(..))
import Reimbursement.Model as ParentModel exposing (Model)
import Reimbursement.Search.Update exposing (Msg(..), update)
import Reimbursement.Update as ParentMsg exposing (Msg(..))


{-| Matches a date un the YYYY-MM-DD format

    matchDate "1970-01-01" --> True

    matchDate "foo-42-01" --> False

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


getField : ParentModel.Model -> Label -> Field
getField model label =
    List.Extra.find (Fields.getLabel >> (==) label) model.searchFields
        |> Maybe.withDefault (Field Empty "")


viewField : ParentModel.Model -> ( Int, ( Label, Field ) ) -> Html ParentMsg.Msg
viewField model ( index, ( label, field ) ) =
    let
        value =
            Fields.getValue field

        base =
            [ Textfield.onInput (Update label >> ParentMsg.SearchMsg)
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
            if Fields.isDate label then
                [ Options.when (Textfield.error validationMsg) (not <| matchDate value) ]
            else
                []

        attrs =
            List.concat [ base, disabled, dateValidation ]
    in
        p []
            [ Options.styled span [ Typography.caption ] [ text <| Fields.getLabelTranslation model.lang field ]
            , br [] []
            , Textfield.render ParentMsg.Mdl [ index ] model.mdl attrs
            ]


viewFieldset : ParentModel.Model -> ( Int, ( TranslationId, List Label ) ) -> Material.Grid.Cell ParentMsg.Msg
viewFieldset model ( index, ( title, labels ) ) =
    let
        fields =
            List.map (getField model) labels

        namesAndFields =
            List.map2 (,) labels fields

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

    correctedFieldIndex 0 42 --> 142

    correctedFieldIndex 100 8 --> 10108

-}
correctedFieldIndex : Int -> Int -> Int
correctedFieldIndex fieldset field =
    ((fieldset + 1) * 100) + field


view : ParentModel.Model -> Html ParentMsg.Msg
view model =
    let
        searchFields =
            grid [] <| List.map (viewFieldset model) Fields.sets

        send =
            searchButton model
                0
                [ Button.raised, Button.colored, Button.type_ "submit" ]
                Search

        showFormButton =
            searchButton model
                1
                [ Button.raised, Button.onClick ToggleForm ]
                NewSearch
    in
        if model.showForm then
            form [ onSubmit Submit ] [ searchFields, send ]
        else
            showFormButton


searchButton : ParentModel.Model -> Int -> List (Button.Property ParentMsg.Msg) -> TranslationId -> Html ParentMsg.Msg
searchButton model index defaultAttr defaultLabel =
    let
        label =
            if model.loading then
                translate model.lang Loading
            else
                translate model.lang defaultLabel

        attr =
            if model.loading then
                Button.disabled :: defaultAttr
            else
                defaultAttr
    in
        grid []
            [ cell [ size Desktop 12, size Tablet 8, size Phone 4 ]
                [ Options.styled div
                    [ Typography.center ]
                    [ Button.render Mdl
                        [ index ]
                        model.mdl
                        attr
                        [ text label ]
                    ]
                ]
            ]
