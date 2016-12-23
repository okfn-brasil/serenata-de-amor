module Documents.Receipt.Update exposing (Msg(..), update)

import Documents.Receipt.Decoder exposing (urlDecoder)
import Documents.Receipt.Model exposing (Model, ReimbursementId)
import Http
import Material
import String
import Task


type Msg
    = LoadUrl (Maybe ReimbursementId)
    | UpdateReimbursementId ReimbursementId
    | ApiSuccess (Maybe String)
    | ApiFail Http.Error
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadUrl (Just reimbursement) ->
            ( { model | loading = True }, loadUrl reimbursement )

        LoadUrl Nothing ->
            ( model, Cmd.none )

        UpdateReimbursementId reimbursement ->
            ( { model | reimbursement = Just reimbursement }, Cmd.none )

        ApiSuccess maybeUrl ->
            ( { model | url = maybeUrl, loading = False, fetched = True }, Cmd.none )

        ApiFail error ->
            let
                err =
                    Debug.log "ApiFail" (toString error)
            in
                ( { model | loading = False, fetched = True, error = Just error }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


loadUrl : ReimbursementId -> Cmd Msg
loadUrl reimbursement =
    let
        query =
            [ ( "format", "json" )
            , ( "force", "true" )
            ]

        path =
            String.join "/"
                [ "/api"
                , "reimbursement"
                , toString reimbursement.year
                , toString reimbursement.applicantId
                , toString reimbursement.documentId
                , "receipt/"
                ]

        url =
            Http.url path query
    in
        Task.perform
            ApiFail
            ApiSuccess
            (Http.get urlDecoder url)
