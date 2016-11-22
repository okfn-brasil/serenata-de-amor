module Documents.Receipt.Update exposing (Msg(..), update)

import Http
import Material
import Task
import Documents.Receipt.Model exposing (Model)
import Documents.Receipt.Decoder exposing (urlDecoder)


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
            let
                err =
                    Debug.log (toString error)
            in
                ( { model | loading = False, fetched = True, error = Just error }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


loadUrl : Int -> Cmd Msg
loadUrl id =
    let
        query =
            [ ( "format", "json" ) ]

        path =
            "/api/receipt/" ++ (toString id)

        url =
            Http.url path query
    in
        Task.perform
            ApiFail
            ApiSuccess
            (Http.get urlDecoder url)
