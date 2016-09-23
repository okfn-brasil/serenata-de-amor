module Template exposing (Model, Msg, header, initialModel, footer)

import Html exposing (a, div, h1, img, li, text, ul)
import Html.Attributes exposing (class, href, src, alt)


--
-- Model
--


type alias Link =
    { label : String
    , url : String
    }


type alias Model =
    { jarbas : Link
    , serenata : Link
    , table : Link
    , digitalOcean : Link
    }


jarbas : Link
jarbas =
    Link "Jarbas" "http://github.com/datasciencebr/jarbas"


serenata : Link
serenata =
    Link "About Serenata de Amor" "http://github.com/datasciencebr/serenata-de-Amor"


table : Link
table =
    Link "Dataset description" "/static/ceap-datasets.html"


digitalOcean : Link
digitalOcean =
    Link "Powered by Digital Ocean" "http://digitalocean.com"


initialModel : Model
initialModel =
    Model jarbas serenata table digitalOcean



--
--
--


type Msg
    = Nothing



--
-- View
--


header : Model -> Html.Html Msg
header model =
    div [ class "header" ] [ h1 [] [ text model.jarbas.label ] ]


footer : Model -> Html.Html Msg
footer model =
    let
        digitalocean =
            a
                [ href model.digitalOcean.url ]
                [ img
                    [ src "/static/digitalocean.png"
                    , alt model.digitalOcean.label
                    ]
                    []
                ]
    in
        div [ class "footer" ]
            [ ul
                []
                [ li [] [ a [ href model.table.url ] [ model.table.label |> text ] ]
                , li [] [ a [ href model.serenata.url ] [ model.serenata.label |> text ] ]
                , li [] [ a [ href model.jarbas.url ] [ "About " ++ model.jarbas.label |> text ] ]
                , li [] [ digitalocean ]
                ]
            ]
