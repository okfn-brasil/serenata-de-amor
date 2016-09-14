module Template exposing (Model, Msg, header, initialModel, footer)

import Html exposing (a, div, h1, li, text, ul)
import Html.Attributes exposing (class, href)


--
-- Model
--


type alias Model =
    { jarbas : String
    , serenata : String
    , github : String
    }


initialModel : Model
initialModel =
    Model "Jarbas" "Serenata de Amor" "http://github.com/datasciencebr/"



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
    div [ class "header" ] [ h1 [] [ text model.jarbas ] ]


footer : Model -> Html.Html a
footer model =
    let
        serenata =
            model.github ++ "serenata-de-amor"

        jarbas =
            model.github ++ "jarbas"
    in
        div [ class "footer" ]
            [ ul
                []
                [ li [] [ a [ href serenata ] [ "About " ++ model.serenata |> text ] ]
                , li [] [ a [ href jarbas ] [ "About " ++ model.jarbas |> text ] ]
                ]
            ]
