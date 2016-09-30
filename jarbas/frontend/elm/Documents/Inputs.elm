module Documents.Inputs exposing (Model, Msg, toQuery, model, update, updateFromQuery, view)

import Dict
import Documents.Fields as Fields
import Html exposing (div, input, label, text)
import Html.Attributes exposing (class, disabled, for, id, type', value)
import Html.Events exposing (onInput, onSubmit)
import String


--
-- Model
--


type alias Field =
    { label : String
    , value : String
    }


type alias Model =
    Dict.Dict String Field


toFormField : ( String, String ) -> ( String, Field )
toFormField ( name, label ) =
    ( name, Field label "" )


model : Model
model =
    let
        pairs =
            List.map2 (,) Fields.names Fields.labels
    in
        List.filter Fields.isSearchable pairs
            |> List.map toFormField
            |> Dict.fromList



--
-- Update
--


type Msg
    = Update String String


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Update name value ->
            ( updateField model ( name, value ), Cmd.none )


updateField : Model -> ( String, String ) -> Model
updateField model ( name, value ) =
    case (Dict.get name model) of
        Just field ->
            Dict.insert name { field | value = value } model

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
toQuery form =
    form
        |> Dict.filter (\index field -> not (String.isEmpty field.value))
        |> Dict.map (\index field -> field.value)
        |> Dict.toList



--
-- View
--


viewField : Bool -> ( String, Field ) -> Html.Html Msg
viewField loading ( name, field ) =
    div
        [ class "field" ]
        [ label [ for <| "id_" ++ name ] [ text field.label ]
        , input
            [ type' "text"
            , id <| "id_" ++ name
            , value field.value
            , Update name |> onInput
            , disabled loading
            ]
            []
        ]


view : Bool -> Model -> List (Html.Html Msg)
view loading model =
    List.map (viewField loading) (Dict.toList model)
