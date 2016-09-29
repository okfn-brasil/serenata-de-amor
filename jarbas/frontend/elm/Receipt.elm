module Receipt exposing (Model, Msg, update, view)

import Html exposing (a, button, div, text)
import Html.Attributes exposing (disabled, href)
import Html.Events exposing (onClick)
import Http
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
    }


initialModel : Model
initialModel =
    { url = Nothing
    , fetched = False
    , loading = False
    , error = Nothing
    }



--
-- Update
--


type Msg
    = LoadUrl Int
    | ApiSuccess (Maybe String)
    | ApiFail Http.Error


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadUrl id ->
            ( { model | loading = True }, loadUrl id )

        ApiSuccess maybeUrl ->
            ( { model | url = maybeUrl, loading = False, fetched = True }, Cmd.none )

        ApiFail error ->
            ( { model | loading = False, fetched = True, error = Just error }, Cmd.none )


loadUrl : Int -> Cmd Msg
loadUrl id =
    let
        url =
            "/api/receipt/" ++ (toString id)
    in
        Task.perform
            ApiFail
            ApiSuccess
            (Http.get decoder url)


decoder : Json.Decode.Decoder (Maybe String)
decoder =
    at [ "url" ] (maybe string)



--
-- View
--


view : Int -> Model -> Html.Html Msg
view id receipt =
    case receipt.url of
        Just url ->
            a [ href url ] [ text url ]

        Nothing ->
            if receipt.fetched then
                div [] [ text "Not available" ]
            else
                let
                    label =
                        if receipt.loading then
                            "Loading…"
                        else
                            "Fetch receipt URL"
                in
                    button
                        [ onClick (LoadUrl id)
                        , disabled receipt.loading
                        ]
                        [ text label ]
