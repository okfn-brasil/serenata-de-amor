module Main exposing (..)

import Html exposing (a, div, h1, li, text, ul)
import Html.App
import Html.Attributes exposing (class, href)
import Navigation
import String
import Document


--
-- Model
--


type alias Model =
    { documents : Document.Model
    , documentCount : Maybe Int
    , documentTotal : Int
    , title : String
    , github :
        { main : String
        , api : String
        }
    }


initialDocumentModel : Document.Model
initialDocumentModel =
    Document.Model [] "" False Nothing


initialModel : Model
initialModel =
    { documents = initialDocumentModel
    , documentCount = Nothing
    , documentTotal = 2072729
    , title = "Serenata de Amor"
    , github =
        { main = "http://github.com/datasciencebr/serenata-de-amor"
        , api = "http://github.com/datasciencebr/jarbas"
        }
    }



--
-- Update
--


type Msg
    = DocumentMsg Document.Msg


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



--
-- View
--


viewWrapper : Html.Html Msg -> Html.Html Msg
viewWrapper html =
    div [ class "outer" ] [ div [ class "inner" ] [ html ] ]


viewHeader : Model -> Html.Html Msg
viewHeader model =
    div [ class "header" ] [ h1 [] [ text model.title ] ]


viewFooter : Model -> Html.Html Msg
viewFooter model =
    div [ class "footer" ]
        [ ul
            []
            [ li [] [ a [ href model.github.main ] [ text <| "About " ++ model.title ] ]
            , li [] [ a [ href model.github.api ] [ text "Fork me on GitHub" ] ]
            , viewPercent model.documentCount model.documentTotal
            ]
        ]


viewPercent : Maybe Int -> Int -> Html.Html Msg
viewPercent count total =
    case count of
        Just documents ->
            let
                percentLoaded =
                    toFloat documents / toFloat total |> (*) 100 |> round |> toString

                link =
                    a
                        [ href "http://www.camara.gov.br/cota-parlamentar/" ]
                        [ text "CEAP" ]
            in
                li []
                    [ text <| percentLoaded ++ "% of "
                    , link
                    , text <| " data loaded"
                    ]

        Nothing ->
            text ""


view : Model -> Html.Html Msg
view model =
    let
        documents =
            Html.App.map DocumentMsg <| Document.view model.documents
    in
        div
            []
            [ viewWrapper <| viewHeader model
            , viewWrapper <| documents
            , viewWrapper <| viewFooter model
            ]



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
                ( { model | documents = initialDocumentModel }, Cmd.none )
            else
                ( model, Cmd.map DocumentMsg <| Document.loadDocuments id )

        Nothing ->
            ( model, Navigation.modifyUrl "" )



--
-- Init
--


type alias Flags =
    { count : Int }


init : Flags -> Maybe String -> ( Model, Cmd Msg )
init flags documentId =
    urlUpdate documentId { initialModel | documentCount = Just flags.count }


main : Platform.Program Flags
main =
    Navigation.programWithFlags urlParser
        { init = init
        , update = update
        , urlUpdate = urlUpdate
        , view = view
        , subscriptions = (\_ -> Sub.none)
        }
