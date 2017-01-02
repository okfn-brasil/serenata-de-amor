module Documents.RelatedTable.Update exposing (Msg(..), getDocumentUrl, loadUrl, update)

import Documents.RelatedTable.Decoder exposing (decoder)
import Documents.RelatedTable.Model exposing (Model, DocumentSummary, Results)
import Http
import Material
import String


type Msg
    = LoadRelatedTable (Result Http.Error Results)
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
        LoadRelatedTable (Ok results) ->
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

        LoadRelatedTable (Err error) ->
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


loadUrl : String -> Cmd Msg
loadUrl url =
    Http.send
        LoadRelatedTable
        (Http.get url decoder)
