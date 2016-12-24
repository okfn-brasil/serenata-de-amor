module Update exposing (Flags, Msg(..), update, urlUpdate, updateFromFlags)

import Documents.Decoder
import Documents.Inputs.Update
import Documents.Update
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Model exposing (Model, model)
import Navigation
import String


type alias Flags =
    { lang : String
    , googleStreetViewApiKey : String
    }


type Msg
    = DocumentsMsg Documents.Update.Msg
    | ChangeUrl Navigation.Location
    | LayoutMsg Msg
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case Debug.log "msg" msg of
        DocumentsMsg msg ->
            let
                updated =
                    Documents.Update.update msg model.documents

                documents =
                    Tuple.first updated

                cmd =
                    Cmd.map DocumentsMsg <| Tuple.second updated
            in
                ( { model | documents = documents }, cmd )

        ChangeUrl location ->
            urlUpdate location model

        LayoutMsg _ ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateFromFlags : Flags -> Model -> Model
updateFromFlags flags model =
    let
        lang =
            if String.toLower flags.lang == "pt" then
                Portuguese
            else
                English

        googleStreetViewApiKey =
            flags.googleStreetViewApiKey

        newDocuments =
            Documents.Decoder.updateLanguage lang model.documents
                |> Documents.Decoder.updateGoogleStreetViewApiKey googleStreetViewApiKey

        layout =
            model.layout

        newLayout =
            { layout | lang = lang }
    in
        { model
            | documents = newDocuments
            , layout = newLayout
            , googleStreetViewApiKey = googleStreetViewApiKey
            , lang = lang
        }


fromHash : String -> List ( String, String )
fromHash hash =
    let
        indexedList =
            String.split "/" hash |> List.drop 1 |> List.indexedMap (,)

        headersAndValues =
            List.partition (\( i, v ) -> rem i 2 == 0) indexedList

        headers =
            Tuple.first headersAndValues |> List.map (\( i, v ) -> v)

        retroCompatibileHeaders =
            List.map
                (\header ->
                    if header == "document" then
                        "documentId"
                    else
                        header
                )
                headers

        values =
            Tuple.second headersAndValues |> List.map (\( i, v ) -> v)
    in
        List.map2 (,) retroCompatibileHeaders values


urlUpdate : Navigation.Location -> Model -> ( Model, Cmd Msg )
urlUpdate location model =
    let
        query =
            fromHash location.hash

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
