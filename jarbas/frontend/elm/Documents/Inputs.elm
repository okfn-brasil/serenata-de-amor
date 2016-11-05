module Documents.Inputs exposing (Model, Msg, model, toQuery, update, updateFromQuery, updateLanguage, view)

import Char
import Dict
import Documents.Fields as Fields
import Html exposing (br, p, span, text)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Material.Grid exposing (grid, cell, size, Device(..))
import Material.Options as Options
import Material.Textfield as Textfield
import Material.Typography as Typography
import String


--
-- Model
--


type alias Field =
    { label : String
    , value : String
    }


type alias Model =
    { inputs : Dict.Dict String Field
    , lang : Language
    , mdl : Material.Model
    }


toFormField : ( String, String ) -> ( String, Field )
toFormField ( name, label ) =
    ( name, Field label "" )


model : Model
model =
    let
        pairs =
            List.map2 (,) Fields.names (Fields.labels English)

        inputs =
            List.filter Fields.isSearchable pairs
                |> List.map toFormField
                |> Dict.fromList
    in
        Model inputs English Material.model



--
-- Update
--


type Msg
    = Update String String
    | Mdl (Material.Msg Msg)


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
                        String.filter Char.isDigit value
                    else if List.member name [ "state", "party" ] then
                        String.map Char.toUpper value
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



--
-- View
--


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
