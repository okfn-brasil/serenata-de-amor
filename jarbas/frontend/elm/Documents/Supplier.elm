module Documents.Supplier exposing (Model, Msg, model, load, update, view)

import Char
import Html exposing (a, br, div, h3, table, td, text, th, tr)
import Html.Attributes exposing (href)
import Http exposing (url)
import Json.Decode exposing ((:=))
import Json.Decode.Pipeline exposing (decode, nullable, required)
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
    , opening : Maybe String
    , legal_entity : Maybe String
    , trade_name : Maybe String
    , name : Maybe String
    , supplier_type : Maybe String
    , status : Maybe String
    , situation : Maybe String
    , situation_reason : Maybe String
    , situation_date : Maybe String
    , special_situation : Maybe String
    , special_situation_date : Maybe String
    , responsible_federative_entity : Maybe String
    , address : Maybe String
    , address_number : Maybe String
    , additional_address_details : Maybe String
    , neighborhood : Maybe String
    , zip_code : Maybe String
    , city : Maybe String
    , state : Maybe String
    , email : Maybe String
    , phone : Maybe String
    , latitude : Maybe String
    , longitude : Maybe String
    , last_updated : Maybe String
    }


type alias Model =
    { supplier : Maybe Supplier
    , loading : Bool
    , loaded : Bool
    , error : Maybe Http.Error
    }


model : Model
model =
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
            ( { model | loaded = True, error = Just error }, Cmd.none )


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
        |> required "opening" (nullable Json.Decode.string)
        |> required "legal_entity" (nullable Json.Decode.string)
        |> required "trade_name" (nullable Json.Decode.string)
        |> required "name" (nullable Json.Decode.string)
        |> required "type" (nullable Json.Decode.string)
        |> required "status" (nullable Json.Decode.string)
        |> required "situation" (nullable Json.Decode.string)
        |> required "situation_reason" (nullable Json.Decode.string)
        |> required "situation_date" (nullable Json.Decode.string)
        |> required "special_situation" (nullable Json.Decode.string)
        |> required "special_situation_date" (nullable Json.Decode.string)
        |> required "responsible_federative_entity" (nullable Json.Decode.string)
        |> required "address" (nullable Json.Decode.string)
        |> required "number" (nullable Json.Decode.string)
        |> required "additional_address_details" (nullable Json.Decode.string)
        |> required "neighborhood" (nullable Json.Decode.string)
        |> required "zip_code" (nullable Json.Decode.string)
        |> required "city" (nullable Json.Decode.string)
        |> required "state" (nullable Json.Decode.string)
        |> required "email" (nullable Json.Decode.string)
        |> required "phone" (nullable Json.Decode.string)
        |> required "latitude" (nullable Json.Decode.string)
        |> required "longitude" (nullable Json.Decode.string)
        |> required "last_updated" (nullable Json.Decode.string)


decodeActivities : Json.Decode.Decoder (List Activity)
decodeActivities =
    Json.Decode.list <|
        Json.Decode.object2 Activity
            (Json.Decode.at [ "code" ] Json.Decode.string)
            (Json.Decode.at [ "description" ] Json.Decode.string)



--
-- View
--


viewGeoCoord : Maybe String -> Maybe String -> Html.Html Msg
viewGeoCoord latitude longitude =
    case latitude of
        Just lat ->
            case longitude of
                Just long ->
                    let
                        coords =
                            lat ++ "," ++ long

                        url =
                            "https://ddg.gg/?q=!gm+" ++ coords
                    in
                        a [ href url ] [ text coords ]

                Nothing ->
                    text ""

        Nothing ->
            text ""


viewSupplier : Supplier -> Html.Html Msg
viewSupplier supplier =
    let
        labels =
            [ ( "CNPJ", supplier.cnpj )
            , ( "Trade name", Maybe.withDefault "" supplier.trade_name )
            , ( "Name", Maybe.withDefault "" supplier.name )
            , ( "Opening date", Maybe.withDefault "" supplier.opening )
            , ( "Legal entity", Maybe.withDefault "" supplier.legal_entity )
            , ( "Type", Maybe.withDefault "" supplier.supplier_type )
            , ( "Status", Maybe.withDefault "" supplier.status )
            , ( "Situation", Maybe.withDefault "" supplier.situation )
            , ( "Situation reason", Maybe.withDefault "" supplier.situation_reason )
            , ( "Situation date", Maybe.withDefault "" supplier.situation_date )
            , ( "Special situation", Maybe.withDefault "" supplier.special_situation )
            , ( "Special situation date", Maybe.withDefault "" supplier.special_situation_date )
            , ( "Responsible federative entity", Maybe.withDefault "" supplier.responsible_federative_entity )
            , ( "Address", Maybe.withDefault "" supplier.address )
            , ( "Number", Maybe.withDefault "" supplier.address_number )
            , ( "Additional address details", Maybe.withDefault "" supplier.additional_address_details )
            , ( "Neighborhood", Maybe.withDefault "" supplier.neighborhood )
            , ( "Zip code", Maybe.withDefault "" supplier.zip_code )
            , ( "City", Maybe.withDefault "" supplier.city )
            , ( "State", Maybe.withDefault "" supplier.state )
            , ( "Email", Maybe.withDefault "" supplier.email )
            , ( "Phone", Maybe.withDefault "" supplier.phone )
            , ( "Last updated", Maybe.withDefault "" supplier.last_updated )
            ]

        activities =
            [ ( "Main activity", supplier.main_activity )
            , ( "Secondary activity", supplier.secondary_activity )
            ]

        stringRows =
            List.map viewRow labels

        activityRows =
            List.map viewActivities activities

        geoCoordRow =
            [ tr
                []
                [ th [] [ text "Latitude & longitude" ]
                , td [] [ viewGeoCoord supplier.latitude supplier.longitude ]
                ]
            ]

        firstRows =
            List.take 3 stringRows

        remainingRows =
            List.drop 3 stringRows

        rows =
            List.concat [ firstRows, activityRows, remainingRows, geoCoordRow ]
    in
        div
            []
            [ h3 [] [ text <| "Supplier: " ++ (Maybe.withDefault "" supplier.name) ]
            , table [] rows
            ]


viewActivity : Activity -> Html.Html Msg
viewActivity activity =
    activity.code ++ " " ++ activity.description |> text


viewActivities : ( String, List Activity ) -> Html.Html Msg
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


viewRow : ( String, String ) -> Html.Html Msg
viewRow ( header, content ) =
    tr
        []
        [ th [] [ text header ]
        , td [] [ text content ]
        ]


view : Model -> Html.Html Msg
view model =
    if model.loaded then
        case model.supplier of
            Just info ->
                viewSupplier info

            Nothing ->
                div
                    []
                    [ br [] []
                    , text "(CNPJ invalid or not found.)"
                    ]
    else if model.loading then
        div
            []
            [ br [] []
            , text "Fetching supplier info from CNPJ…"
            ]
    else
        text ""
