module Routes exposing (urlParser, urlUpdate)

import Documents.Update
import Documents.Decoder
import Documents.Inputs.Update
import Navigation
import String
import Model exposing (Model)
import Update exposing (Msg(..))


fromUrl : String -> List ( String, String )
fromUrl hash =
    let
        indexedList =
            String.split "/" hash |> List.drop 1 |> List.indexedMap (,)

        headersAndValues =
            List.partition (\( i, v ) -> i `rem` 2 == 0) indexedList

        headers =
            fst headersAndValues |> List.map (\( i, v ) -> v)

        retroCompatibileHeaders =
            List.map
                (\header ->
                    if header == "document" then
                        "document_id"
                    else
                        header
                )
                headers

        values =
            snd headersAndValues |> List.map (\( i, v ) -> v)
    in
        List.map2 (,) retroCompatibileHeaders values


urlParser : Navigation.Parser (List ( String, String ))
urlParser =
    Navigation.makeParser (fromUrl << .hash)


urlUpdate : List ( String, String ) -> Model -> ( Model, Cmd Msg )
urlUpdate query model =
    let
        loading =
            if List.isEmpty query then
                False
            else
                True

        documents =
            if List.isEmpty query then
                Documents.Update.newSearch model.documents
            else
                model.documents

        inputs =
            Documents.Inputs.Update.updateFromQuery documents.inputs query

        results =
            documents.results

        newResults =
            { results | loadingPage = Documents.Decoder.getPage query }

        newDocuments =
            { documents | inputs = inputs, results = newResults, loading = loading }

        cmd =
            Documents.Update.loadDocuments model.lang model.googleStreetViewApiKey query
    in
        ( { model | documents = newDocuments }, Cmd.map DocumentsMsg cmd )
