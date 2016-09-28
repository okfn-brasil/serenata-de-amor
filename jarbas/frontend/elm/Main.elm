module Main exposing (..)

import Document
import Html exposing (a, div, h1, li, text, ul)
import Html.App
import Html.Attributes exposing (class, href)
import Navigation
import String
import Template


--
-- Model
--


type alias Model =
    { documents : Document.Model
    , template : Template.Model
    }


initialModel : Model
initialModel =
    { documents = Document.initialModel
    , template = Template.initialModel
    }



--
-- Update
--


type Msg
    = DocumentMsg Document.Msg
    | TemplateMsg Template.Msg


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        DocumentMsg msg ->
            let
                updated =
                    Document.update msg model.documents

                documents =
                    fst updated

                cmd =
                    Cmd.map DocumentMsg <| snd updated
            in
                ( { model | documents = documents }, cmd )

        TemplateMsg _ ->
            ( model, Cmd.none )



--
-- View
--


viewWrapper : Html.Html a -> Html.Html a
viewWrapper html =
    div [ class "outer" ] [ div [ class "inner" ] [ html ] ]


view : Model -> Html.Html Msg
view model =
    let
        documents =
            Html.App.map DocumentMsg <| Document.view model.documents

        header =
            Html.App.map TemplateMsg <| Template.header model.template

        footer =
            Html.App.map TemplateMsg <| Template.footer model.template
    in
        div [] (List.map viewWrapper [ header, documents, footer ])



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
        ( { model | documents = Document.initialModel }
        , Cmd.none
        )
    else
        let
            documents =
                model.documents

            form =
                documents.form

            newDocuments =
                { documents | form = Document.updateFormFields form query }
        in
            ( { model | documents = newDocuments }
            , Cmd.map DocumentMsg <| Document.loadDocuments query
            )


type alias Flags =
    { count : Int }


init : List ( String, String ) -> ( Model, Cmd Msg )
init documentId =
    urlUpdate documentId initialModel


main : Platform.Program Never
main =
    Navigation.program urlParser
        { init = init
        , update = update
        , urlUpdate = urlUpdate
        , view = view
        , subscriptions = (\_ -> Sub.none)
        }
