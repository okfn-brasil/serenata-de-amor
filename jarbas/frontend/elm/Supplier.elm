module Supplier exposing (Model, Msg, initialModel, load, update, view)

import Char
import Html exposing (br, div, h3, table, td, text, th, tr)
import Http
import Json.Decode exposing ((:=))
import Json.Decode.Pipeline exposing (decode, hardcoded, required)
import String
import Task


--
-- Model
--


type alias Activity =
    { code : String
    , description : String
    }


type alias Supplier =
    { main_activity : List Activity
    , secondary_activity : List Activity
    , cnpj : String
    , opening : String
    , legal_entity : String
    , trade_name : String
    , name : String
    , supplier_type : String
    , status : String
    , situation : String
    , situation_reason : String
    , situation_date : String
    , special_situation : String
    , special_situation_date : Maybe String
    , responsible_federative_entity : String
    , address : String
    , address_number : String
    , additional_address_details : String
    , neighborhood : String
    , zip_code : String
    , city : String
    , state : String
    , email : String
    , phone : String
    , last_updated : String
    }


type alias Model =
    { supplier : Maybe Supplier
    , loading : Bool
    , loaded : Bool
    , error : Maybe Http.Error
    }


initialModel : Model
initialModel =
    { supplier = Nothing
    , loading = False
    , loaded = False
    , error = Nothing
    }



--
-- Update
--


type Msg
    = LoadSupplier String
    | ApiSuccess Supplier
    | ApiFail Http.Error


cleanUp : String -> String
cleanUp cnpj =
    String.filter Char.isDigit cnpj


isValid : String -> Bool
isValid cnpj =
    if String.length (cleanUp cnpj) == 14 then
        True
    else
        False


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadSupplier cnpj ->
            if isValid cnpj then
                ( { model | loading = True }, load cnpj )
            else
                ( { model | loaded = True, supplier = Nothing }, Cmd.none )

        ApiSuccess supplier ->
            ( { model | supplier = Just supplier, loading = False, loaded = True }, Cmd.none )

        ApiFail error ->
            ( { initialModel | loaded = True, error = Just error }, Cmd.none )


load : String -> Cmd Msg
load cnpj =
    let
        url =
            "/api/supplier/" ++ cleanUp cnpj
    in
        Task.perform
            ApiFail
            ApiSuccess
            (Http.get decoder url)



--
-- Decoder
--


decoder : Json.Decode.Decoder Supplier
decoder =
    decode Supplier
        |> required "main_activity" decodeActivities
        |> required "secondary_activity" decodeActivities
        |> required "cnpj" Json.Decode.string
        |> required "opening" Json.Decode.string
        |> required "legal_entity" Json.Decode.string
        |> required "trade_name" Json.Decode.string
        |> required "name" Json.Decode.string
        |> required "type" Json.Decode.string
        |> required "status" Json.Decode.string
        |> required "situation" Json.Decode.string
        |> required "situation_reason" Json.Decode.string
        |> required "situation_date" Json.Decode.string
        |> required "special_situation" Json.Decode.string
        |> required "special_situation_date" (Json.Decode.Pipeline.nullable Json.Decode.string)
        |> required "responsible_federative_entity" Json.Decode.string
        |> required "address" Json.Decode.string
        |> required "number" Json.Decode.string
        |> required "additional_address_details" Json.Decode.string
        |> required "neighborhood" Json.Decode.string
        |> required "zip_code" Json.Decode.string
        |> required "city" Json.Decode.string
        |> required "state" Json.Decode.string
        |> required "email" Json.Decode.string
        |> required "phone" Json.Decode.string
        |> required "last_updated" Json.Decode.string


decodeActivities : Json.Decode.Decoder (List Activity)
decodeActivities =
    Json.Decode.list <|
        Json.Decode.object2 Activity
            (Json.Decode.at [ "code" ] Json.Decode.string)
            (Json.Decode.at [ "description" ] Json.Decode.string)



--
-- View
--


viewSupplier : Supplier -> Html.Html a
viewSupplier supplier =
    let
        labels =
            [ ( "CNPJ", supplier.cnpj )
            , ( "Trade name", supplier.trade_name )
            , ( "Name", supplier.name )
            , ( "Opening date", supplier.opening )
            , ( "Legal entity", supplier.legal_entity )
            , ( "Type", supplier.supplier_type )
            , ( "Status", supplier.status )
            , ( "Situation", supplier.situation )
            , ( "Situation reason", supplier.situation_reason )
            , ( "Situation date", supplier.situation_date )
            , ( "Special situation", supplier.special_situation )
            , ( "Special situation date", Maybe.withDefault "" supplier.special_situation_date )
            , ( "Responsible federative entity", supplier.responsible_federative_entity )
            , ( "Address", supplier.address )
            , ( "Number", supplier.address_number )
            , ( "Additional address details", supplier.additional_address_details )
            , ( "Neighborhood", supplier.neighborhood )
            , ( "Zip code", supplier.zip_code )
            , ( "City", supplier.city )
            , ( "State", supplier.state )
            , ( "Email", supplier.email )
            , ( "Phone", supplier.phone )
            , ( "Last updated", supplier.last_updated )
            ]

        activities =
            [ ( "Main activity", supplier.main_activity )
            , ( "Secondary activity", supplier.secondary_activity )
            ]

        stringRows =
            List.map viewRow labels

        activityRows =
            List.map viewActivities activities

        firstRows =
            List.take 3 stringRows

        remainingRows =
            List.drop 3 stringRows

        rows =
            List.concat [ firstRows, activityRows, remainingRows ]
    in
        div
            []
            [ h3 [] [ text <| "Supplier: " ++ (supplier.name) ]
            , table [] rows
            ]


viewActivity : Activity -> Html.Html a
viewActivity activity =
    activity.code ++ " " ++ activity.description |> text


viewActivities : ( String, List Activity ) -> Html.Html a
viewActivities ( label, activities ) =
    let
        texts =
            List.map viewActivity activities

        contents =
            List.intersperse (br [] []) texts
    in
        tr
            []
            [ th [] [ text label ]
            , td [] contents
            ]


viewRow : ( String, String ) -> Html.Html a
viewRow ( header, content ) =
    tr
        []
        [ th [] [ text header ]
        , td [] [ text content ]
        ]


view : Model -> Html.Html a
view model =
    if model.loaded then
        case model.supplier of
            Just info ->
                viewSupplier info

            Nothing ->
                text "CNPJ invalid or not found"
    else if model.loading then
        text "Fetching supplier info…"
    else
        text ""
