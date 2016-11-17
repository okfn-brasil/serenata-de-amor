module Documents.Supplier exposing (Model, Msg, model, load, update, view)

import Char
import Html exposing (a, br, div, img, p, span, text)
import Html.Attributes exposing (href, src, style)
import Http exposing (url)
import Json.Decode exposing ((:=))
import Json.Decode.Pipeline exposing (decode, nullable, required)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Material.Icon as Icon
import Material.Options as Options
import Material.Typography as Typography
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
    , googleStreetViewApiKey : String
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model Nothing False False Nothing "" English Material.model



--
-- Update
--


type Msg
    = LoadSupplier String
    | ApiSuccess Supplier
    | ApiFail Http.Error
    | Mdl (Material.Msg Msg)


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
            let
                err =
                    Debug.log (toString error)
            in
                ( { model | loaded = True, error = Just error }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


load : String -> Cmd Msg
load cnpj =
    let
        query =
            [ ( "format", "json" ) ]

        path =
            "/api/supplier/" ++ (cleanUp cnpj)

        url =
            Http.url path query
    in
        if path == "/api/supplier/" then
            Cmd.none
        else
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


streetImageUrl : String -> Int -> Int -> String -> String -> Int -> String
streetImageUrl apiKey width height latitude longitude heading =
    url
        "https://maps.googleapis.com/maps/api/streetview"
        [ ( "size", (toString width) ++ "x" ++ (toString height) )
        , ( "location", latitude ++ "," ++ longitude )
        , ( "fov", "90" )
        , ( "heading", toString heading )
        , ( "pitch", "10" )
        , ( "key", apiKey )
        ]


streetImageTag : String -> Maybe String -> Maybe String -> Int -> Html.Html Msg
streetImageTag apiKey latitude longitude heading =
    case latitude of
        Just lat ->
            case longitude of
                Just long ->
                    let
                        source =
                            streetImageUrl apiKey 640 400 lat long heading

                        css =
                            [ ( "width", "50%" )
                            , ( "display", "inline-block" )
                            , ( "margin", "1rem 0 0 0" )
                            ]
                    in
                        a
                            [ href source ]
                            [ img [ src source, style css ] [] ]

                Nothing ->
                    text ""

        Nothing ->
            text ""


viewImage : String -> Supplier -> Html.Html Msg
viewImage apiKey supplier =
    let
        images =
            List.map
                (streetImageTag apiKey supplier.latitude supplier.longitude)
                [ 90, 180, 270, 360 ]
    in
        div [] images


viewSupplier : Language -> String -> Supplier -> Html.Html Msg
viewSupplier lang apiKey supplier =
    let
        labels =
            [ ( (translate lang SupplierCNPJ), supplier.cnpj )
            , ( (translate lang SupplierTradeName), Maybe.withDefault "" supplier.trade_name )
            , ( (translate lang SupplierName), Maybe.withDefault "" supplier.name )
            , ( (translate lang SupplierOpeningDate), Maybe.withDefault "" supplier.opening )
            , ( (translate lang SupplierLegalEntity), Maybe.withDefault "" supplier.legal_entity )
            , ( (translate lang SupplierType), Maybe.withDefault "" supplier.supplier_type )
            , ( (translate lang SupplierStatus), Maybe.withDefault "" supplier.status )
            , ( (translate lang SupplierSituation), Maybe.withDefault "" supplier.situation )
            , ( (translate lang SupplierSituationReason), Maybe.withDefault "" supplier.situation_reason )
            , ( (translate lang SupplierSituationDate), Maybe.withDefault "" supplier.situation_date )
            , ( (translate lang SupplierSpecialSituation), Maybe.withDefault "" supplier.special_situation )
            , ( (translate lang SupplierSpecialSituationDate), Maybe.withDefault "" supplier.special_situation_date )
            , ( (translate lang SupplierResponsibleFederativeEntity), Maybe.withDefault "" supplier.responsible_federative_entity )
            , ( (translate lang SupplierAddress), Maybe.withDefault "" supplier.address )
            , ( (translate lang SupplierNumber), Maybe.withDefault "" supplier.address_number )
            , ( (translate lang SupplierAdditionalAddressDetails), Maybe.withDefault "" supplier.additional_address_details )
            , ( (translate lang SupplierNeighborhood), Maybe.withDefault "" supplier.neighborhood )
            , ( (translate lang SupplierZipCode), Maybe.withDefault "" supplier.zip_code )
            , ( (translate lang SupplierCity), Maybe.withDefault "" supplier.city )
            , ( (translate lang SupplierState), Maybe.withDefault "" supplier.state )
            , ( (translate lang SupplierEmail), Maybe.withDefault "" supplier.email )
            , ( (translate lang SupplierPhone), Maybe.withDefault "" supplier.phone )
            , ( (translate lang SupplierLastUpdated), Maybe.withDefault "" supplier.last_updated )
            ]

        rows =
            List.map viewRow labels

        activities =
            List.map
                viewActivities
                [ ( (translate lang SupplierMainActivity), supplier.main_activity )
                , ( (translate lang SupplierSecondaryActivity), supplier.secondary_activity )
                ]

        icon =
            Icon.view "store" [ Options.css "transform" "translateY(0.4rem)" ]

        title =
            " " ++ (Maybe.withDefault "" supplier.name)

        source =
            "http://www.receita.fazenda.gov.br/PessoaJuridica/CNPJ/cnpjreva/cnpjreva_solicitacao2.asp"
    in
        div
            []
            [ Options.styled
                p
                [ Typography.subhead ]
                [ icon, text title, viewImage apiKey supplier ]
            , Options.styled div [] (rows ++ activities)
            , Options.styled
                p
                [ Typography.caption, Options.css "margin-top" "1rem" ]
                [ text (translate lang SupplierSource)
                , a [ href source ] [ text (translate lang SupplierFederalRevenue) ]
                ]
            ]


viewRow : ( String, String ) -> Html.Html Msg
viewRow ( label, value ) =
    let
        styles =
            [ Options.css "display" "flex"
            , Options.css "justify-content" "space-between"
            , Options.css "align-items" "center"
            ]

        labelStyles =
            Options.css "width" "30%" :: styles
    in
        Options.styled div
            [ Options.css "display" "flex"
            , Options.css "flex-direction" "row"
            ]
            [ Options.styled span (Typography.body2 :: labelStyles) [ text label ]
            , Options.styled span (Typography.body1 :: styles) [ text value ]
            ]


viewActivity : Activity -> Html.Html Msg
viewActivity activity =
    activity.code ++ " " ++ activity.description |> text


viewActivities : ( String, List Activity ) -> Html.Html Msg
viewActivities ( label, activities ) =
    let
        value =
            List.map viewActivity activities
                |> List.intersperse (br [] [])
    in
        Options.styled div
            []
            [ Options.styled span [ Typography.body2 ] [ text label ]
            , br [] []
            , Options.styled span [ Typography.body1 ] value
            ]


view : Model -> Html.Html Msg
view model =
    if model.loaded then
        case model.supplier of
            Just info ->
                viewSupplier model.lang model.googleStreetViewApiKey info

            Nothing ->
                Options.styled div
                    [ Typography.caption ]
                    [ text "CNPJ invalid or not found." ]
    else if model.loading then
        Options.styled div
            [ Typography.caption ]
            [ text "Fetching supplier info from CNPJ…" ]
    else
        text ""
