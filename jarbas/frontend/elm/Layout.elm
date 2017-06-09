module Layout exposing (Model, drawer, header, model)

import Html exposing (a, div, img, text)
import Html.Attributes exposing (alt, href, src, style)
import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..))
import Material
import Material.Layout as Layout


--
-- Model
--


type alias Model =
    { lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model English Material.model



--
-- View
--


header : Model -> Html.Html a
header model =
    let
        digitalOcean =
            Layout.link
                [ Layout.href "http://digitalocean.com" ]
                [ img
                    [ src "/static/digitalocean.png"
                    , alt "Powered by Digital Ocean"
                    , style [ ( "height", "1.5rem" ), ( "opacity", "0.5" ) ]
                    ]
                    []
                ]

        title =
            a
                [ href "/"
                , style
                    [ ( "color", "white" )
                    , ( "text-decoration", "none" )
                    , ( "font-weight", "normal" )
                    ]
                ]
                [ text "Jarbas" ]
    in
        Layout.row
            []
            [ Layout.title [] [ title ]
            , Layout.spacer
            , Layout.navigation [] [ digitalOcean ]
            ]


drawerLinks : ( String, String ) -> Html.Html a
drawerLinks ( url, content ) =
    Layout.link [ Layout.href url ] [ text content ]


drawer : Model -> List (Html.Html a)
drawer model =
    [ Layout.title [] [ text (translate model.lang AboutJarbas) ]
    , Layout.navigation [] <|
        List.map
            drawerLinks
            [ ( "/static/ceap-datasets.html", translate model.lang AboutDatasets )
            , ( "http://github.com/datasciencebr/jarbas", translate model.lang AboutJarbas )
            , ( "https://serenatadeamor.org", translate model.lang AboutSerenata )
            ]
    ]
