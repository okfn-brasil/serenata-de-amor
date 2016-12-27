module Documents.SameDay.Update exposing (Msg(..), getUrl, getDocumentUrl, load, update)

import Documents.SameDay.Decoder exposing (decoder)
import Documents.SameDay.Model exposing (Model, DocumentSummary, Results, UniqueId)
import Http
import Material
import String


type Msg
    = LoadSameDay (Result Http.Error Results)
    | MouseOver Int Bool
    | Mdl (Material.Msg Msg)


updateDocument : Int -> Bool -> ( Int, DocumentSummary ) -> DocumentSummary
updateDocument target mouseOver ( index, document ) =
    if target == index then
        { document | over = mouseOver }
    else
        document


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoadSameDay (Ok results) ->
            let
                newDocuments =
                    List.append model.results.documents results.documents

                nextPageUrl =
                    results.nextPageUrl

                newResults =
                    { documents = newDocuments, nextPageUrl = nextPageUrl }

                cmd =
                    case nextPageUrl of
                        Just url ->
                            loadUrl url

                        Nothing ->
                            Cmd.none
            in
                ( { model | results = newResults }, cmd )

        LoadSameDay (Err error) ->
            let
                err =
                    Debug.log "ApiFail" (toString error)
            in
                ( model, Cmd.none )

        MouseOver target mouseOver ->
            let
                newDocuments =
                    model.results.documents
                        |> List.indexedMap (,)
                        |> List.map (updateDocument target mouseOver)

                results =
                    model.results

                newResults =
                    { results | documents = newDocuments }
            in
                ( { model | results = newResults }, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


getDocumentUrl : DocumentSummary -> String
getDocumentUrl document =
    String.join
        "/"
        [ "#"
        , "year"
        , document.year |> toString
        , "applicantId"
        , document.applicantId |> toString
        , "documentId"
        , document.documentId |> toString
        ]


{-| Creates an URL from an UniqueId:

    >>> getUrl { year = 2016, applicantId = 13,  documentId = 42 }
    "/api/reimbursement/2016/13/42/same_day/?format=json"

-}
getUrl : UniqueId -> String
getUrl uniqueId =
    String.join
        "/"
        [ "/api"
        , "reimbursement"
        , uniqueId.year |> toString
        , uniqueId.applicantId |> toString
        , uniqueId.documentId |> toString
        , "same_day/?format=json"
        ]


loadUrl : String -> Cmd Msg
loadUrl url =
    Http.send
        LoadSameDay
        (Http.get url decoder)


load : UniqueId -> Cmd Msg
load uniqueId =
    uniqueId
        |> getUrl
        |> loadUrl
