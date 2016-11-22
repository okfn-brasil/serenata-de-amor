module Documents.Inputs.View exposing (view)

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


getField : Model -> String -> Field
getField model name =
    Maybe.withDefault
        (Field "" "")
        (Dict.get name model.inputs)


viewField : Material.Model -> Bool -> ( Int, ( String, Field ) ) -> Html.Html Msg
viewField mdl loading ( index, ( name, field ) ) =
    let
        base =
            [ Textfield.onInput (Update name)
            , Textfield.value field.value
            , Options.css "padding-top" "0"
            , Options.css "width" "100%"
            ]

        attrs =
            if loading then
                base ++ [ Textfield.disabled ]
            else
                base
    in
        p []
            [ Options.styled span [ Typography.caption ] [ text field.label ]
            , br [] []
            , Textfield.render Mdl [ index ] mdl attrs
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
            List.map (viewField model.mdl loading) indexedNamesAndFields
    in
        cell
            [ size Desktop 4, size Tablet 4, size Phone 4 ]
            (List.append heading inputs)


correctedFieldIndex : Int -> Int -> Int
correctedFieldIndex fieldset field =
    ((fieldset + 1) * 100) + field


view : Bool -> Model -> Html.Html Msg
view loading model =
    grid [] <| List.map (viewFieldset loading model) (Fields.sets model.lang)
