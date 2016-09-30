module Template exposing (Model, drawer, header, initialModel)

import Html exposing (a, text, img)
import Html.Attributes exposing (alt, src, style)
import Material
import Material.Layout as Layout


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
    , mdl : Material.Model
    }


jarbas : Link
jarbas =
    Link "Jarbas" "http://github.com/datasciencebr/jarbas"


serenata : Link
serenata =
    Link "About Serenata de Amor" "http://serenata.datasciencebr.com/"


table : Link
table =
    Link "Dataset description" "/static/ceap-datasets.html"


digitalOcean : Link
digitalOcean =
    Link "Powered by Digital Ocean" "http://digitalocean.com"


initialModel : Model
initialModel =
    Model jarbas serenata table digitalOcean Material.model



--
-- View
--


header : Model -> Html.Html a
header model =
    let
        digitalOceanLogo =
            img
                [ src "/static/digitalocean.png"
                , alt model.digitalOcean.label
                , style [ ( "height", "1.5rem" ), ( "opacity", "0.5" ) ]
                ]
                []
    in
        Layout.row
            []
            [ Layout.title
                []
                [ text model.jarbas.label ]
            , Layout.spacer
            , Layout.navigation []
                [ Layout.link
                    [ Layout.href model.digitalOcean.url ]
                    [ digitalOceanLogo ]
                ]
            ]


drawerLinks : ( String, Html.Html a ) -> Html.Html a
drawerLinks ( url, content ) =
    Layout.link [ Layout.href url ] [ content ]


drawer : Model -> List (Html.Html a)
drawer model =
    [ Layout.title [] [ text "About" ]
    , Layout.navigation [] <|
        List.map
            drawerLinks
            [ ( model.table.url, text model.table.label )
            , ( model.jarbas.url, text <| "About " ++ model.jarbas.label )
            , ( model.serenata.url, text model.serenata.label )
            ]
    ]
