module Main exposing (..)

import Documents
import Documents.Inputs as Inputs
import Html
import Html.App
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Layout
import Material
import Material.Layout
import Navigation
import String


--
-- Model
--


type alias Model =
    { documents : Documents.Model
    , layout : Layout.Model
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model Documents.model Layout.model English Material.model



--
-- Update
--


type Msg
    = DocumentsMsg Documents.Msg
    | LayoutMsg Msg
    | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        DocumentsMsg msg ->
            let
                updated =
                    Documents.update msg model.documents

                documents =
                    fst updated

                cmd =
                    Cmd.map DocumentsMsg <| snd updated
            in
                ( { model | documents = documents }, cmd )

        LayoutMsg _ ->
            ( model, Cmd.none )

        Mdl mdlMsg ->
            Material.update mdlMsg model


updateLanguage : Language -> Model -> Model
updateLanguage lang model =
    let
        newDocuments =
            Documents.updateLanguage lang model.documents

        layout =
            model.layout

        newLayout =
            { layout | lang = lang }
    in
        { model
            | documents = newDocuments
            , layout = newLayout
            , lang = lang
        }



--
-- View
--


view : Model -> Html.Html Msg
view model =
    let
        header =
            Html.App.map LayoutMsg <| Layout.header model.layout

        drawer =
            List.map (\x -> Html.App.map LayoutMsg x) (Layout.drawer model.layout)

        documents =
            Html.App.map DocumentsMsg <| Documents.view model.documents
    in
        Material.Layout.render
            Mdl
            model.mdl
            [ Material.Layout.fixedHeader ]
            { header = [ header ]
            , drawer = drawer
            , tabs = ( [], [] )
            , main = [ documents ]
            }



--
-- URL handling
--


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
            model.documents

        inputs =
            Inputs.updateFromQuery documents.inputs query

        results =
            documents.results

        newResults =
            { results | loadingPage = Documents.getPage query }

        newDocuments =
            { documents | inputs = inputs, results = newResults, loading = loading }

        cmd =
            Documents.loadDocuments query |> Cmd.map DocumentsMsg
    in
        ( { model | documents = newDocuments }, cmd )



--
-- Main
--


type alias Flags =
    { lang : String }


init : Flags -> List ( String, String ) -> ( Model, Cmd Msg )
init flags query =
    let
        lang =
            if String.toLower flags.lang == "pt" then
                Portuguese
            else
                English
    in
        urlUpdate query (updateLanguage lang model)


main : Platform.Program Flags
main =
    Navigation.programWithFlags urlParser
        { init = init
        , update = update
        , urlUpdate = urlUpdate
        , view = view
        , subscriptions = (\_ -> Sub.none)
        }
