module Documents.Receipt.Update exposing (Msg(..), update)

import Documents.Receipt.Decoder exposing (urlDecoder)
import Documents.Receipt.Model exposing (Model, ReimbursementId)
import Format.Url exposing (url)
import Http
import Material
import String


type Msg
    = UpdateReimbursementId ReimbursementId
    | SearchReceipt (Maybe ReimbursementId)
    | LoadReceipt (Result Http.Error (Maybe String))
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        UpdateReimbursementId reimbursement ->
            ( { model | reimbursement = Just reimbursement }, Cmd.none )

        SearchReceipt (Just reimbursement) ->
            ( { model | loading = True }, loadUrl reimbursement )

        SearchReceipt Nothing ->
            ( model, Cmd.none )

        LoadReceipt (Ok maybeUrl) ->
            ( { model | url = maybeUrl, loading = False, fetched = True }, Cmd.none )

        LoadReceipt (Err error) ->
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
    in
        urlDecoder
            |> Http.get (url path query)
            |> Http.send LoadReceipt
