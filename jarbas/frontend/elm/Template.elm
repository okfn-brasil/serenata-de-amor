module Template exposing (Model, Msg, header, initialModel, footer)

import Html exposing (a, div, h1, li, text, ul)
import Html.Attributes exposing (class, href)


--
-- Model
--


type alias Model =
    { title : String
    , github : String
    }


initialModel : Model
initialModel =
    Model "Serenata de Amor" "http://github.com/datasciencebr/"



--
--
--


type Msg
    = Nothing



--
-- View
--


header : Model -> Html.Html a
header model =
    div [ class "header" ] [ h1 [] [ text model.title ] ]


footer : Model -> Html.Html a
footer model =
    let
        about =
            "About " ++ model.title

        serenata =
            model.github ++ "serenata-de-amor"

        jarbas =
            model.github ++ "jarbas"
    in
        div [ class "footer" ]
            [ ul
                []
                [ li [] [ a [ href serenata ] [ text about ] ]
                , li [] [ a [ href jarbas ] [ text "Fork me on GitHub" ] ]
                ]
            ]
