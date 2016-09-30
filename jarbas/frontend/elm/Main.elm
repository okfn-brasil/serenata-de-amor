module Main exposing (..)

import Documents
import Documents.Inputs as Inputs
import Html
import Html.App
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
    , template : Layout.Model
    , mdl : Material.Model
    }


model : Model
model =
    { documents = Documents.model
    , template = Layout.model
    , mdl = Material.model
    }



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



--
-- View
--


view : Model -> Html.Html Msg
view model =
    let
        header =
            Html.App.map LayoutMsg <| Layout.header model.template

        drawer =
            List.map (\x -> Html.App.map LayoutMsg x) (Layout.drawer model.template)

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
    if List.isEmpty query then
        ( { model | documents = Documents.model }
        , Cmd.none
        )
    else
        let
            documents =
                model.documents

            inputs =
                documents.inputs

            newDocumentss =
                { documents | inputs = Inputs.updateFromQuery inputs query }
        in
            ( { model | documents = newDocumentss }
            , Cmd.map DocumentsMsg <| Documents.loadDocuments query
            )


type alias Flags =
    { count : Int }


init : List ( String, String ) -> ( Model, Cmd Msg )
init documentId =
    urlUpdate documentId model


main : Platform.Program Never
main =
    Navigation.program urlParser
        { init = init
        , update = update
        , urlUpdate = urlUpdate
        , view = view
        , subscriptions = (\_ -> Sub.none)
        }
