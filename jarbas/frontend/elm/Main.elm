module Main exposing (..)

import Html exposing (a, div, h1, li, text, ul)
import Html.App
import Html.Attributes exposing (class, href)
import Navigation
import String
import Document
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


toUrl : String -> String
toUrl documentId =
    if documentId == "" then
        ""
    else
        "#/document/" ++ documentId


fromUrl : String -> Maybe String
fromUrl url =
    String.split "/" url |> List.reverse |> List.head


urlParser : Navigation.Parser (Maybe String)
urlParser =
    Navigation.makeParser (fromUrl << .hash)


urlUpdate : Maybe String -> Model -> ( Model, Cmd Msg )
urlUpdate query model =
    case query of
        Just id ->
            if id == "" then
                ( { model | documents = Document.initialModel }, Cmd.none )
            else
                ( model, Cmd.map DocumentMsg <| Document.loadDocuments id )

        Nothing ->
            ( model, Navigation.modifyUrl "" )



--
-- Init
--


type alias Flags =
    { count : Int }


init : Maybe String -> ( Model, Cmd Msg )
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
