module Documents.Receipt exposing (Model, Msg, decoder, update, view)

import Html exposing (a, button, div, text)
import Html.Attributes exposing (href)
import Http
import Json.Decode
import Json.Decode.Pipeline exposing (decode, hardcoded, nullable, required)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Material.Button as Button
import Material.Icon as Icon
import Material.Spinner as Spinner
import Json.Decode exposing (at, maybe, string)
import Task


--
-- Model
--


type alias Model =
    { url : Maybe String
    , fetched : Bool
    , loading : Bool
    , error : Maybe Http.Error
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model Nothing False False Nothing English Material.model



--
-- Update
--


type Msg
    = LoadUrl Int
    | ApiSuccess (Maybe String)
    | ApiFail Http.Error
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadUrl id ->
            ( { model | loading = True }, loadUrl id )

        ApiSuccess maybeUrl ->
            ( { model | url = maybeUrl, loading = False, fetched = True }, Cmd.none )

        ApiFail error ->
            ( { model | loading = False, fetched = True, error = Just error }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


loadUrl : Int -> Cmd Msg
loadUrl id =
    let
        url =
            "/api/receipt/" ++ (toString id)
    in
        Task.perform
            ApiFail
            ApiSuccess
            (Http.get urlDecoder url)



--
-- Decoders
--


urlDecoder : Json.Decode.Decoder (Maybe String)
urlDecoder =
    at [ "url" ] (maybe string)


decoder : Language -> Json.Decode.Decoder Model
decoder lang =
    decode Model
        |> required "url" (nullable Json.Decode.string)
        |> required "fetched" Json.Decode.bool
        |> hardcoded False
        |> hardcoded Nothing
        |> hardcoded lang
        |> hardcoded Material.model



--
-- View
--


view : Int -> Model -> Html.Html Msg
view id model =
    case model.url of
        Just url ->
            a
                [ href url ]
                [ Button.render
                    Mdl
                    [ 1 ]
                    model.mdl
                    [ Button.minifab ]
                    [ Icon.i "receipt"
                    , text (translate model.lang ReceiptAvailable)
                    ]
                ]

        Nothing ->
            if model.fetched then
                div [] [ text (translate model.lang ReceiptNotAvailable) ]
            else if model.loading then
                div [] [ Spinner.spinner [ Spinner.active True ] ]
            else
                Button.render Mdl
                    [ 0 ]
                    model.mdl
                    [ Button.minifab
                    , Button.onClick (LoadUrl id)
                    ]
                    [ Icon.i "search"
                    , text (translate model.lang ReceiptFetch)
                    ]
