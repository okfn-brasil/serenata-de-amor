module Documents.Map exposing (modelFrom, view)

import Documents.Supplier as Supplier
import Material
import Material.Button as Button
import Material.Icon as Icon
import Html exposing (a, text)
import Html.Attributes exposing (href)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import String


--
-- Model
--


type alias GeoCoord =
    { latitude : Maybe String
    , longitude : Maybe String
    }


type alias Model =
    { geoCoord : GeoCoord
    , lang : Language
    , mdl : Material.Model
    }


modelFrom : Language -> Supplier.Model -> Model
modelFrom lang model =
    case model.supplier of
        Just supplier ->
            Model
                { latitude = supplier.latitude
                , longitude = supplier.longitude
                }
                lang
                Material.model

        Nothing ->
            Model
                { latitude = Nothing
                , longitude = Nothing
                }
                lang
                Material.model



--
-- Update
--


type Msg
    = Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Mdl mdlMsg ->
            Material.update mdlMsg model



--
-- View
--


view : Model -> Html.Html Msg
view model =
    case model.geoCoord.latitude of
        Just lat ->
            case model.geoCoord.longitude of
                Just long ->
                    let
                        mapUrl =
                            String.concat [ "https://ddg.gg/?q=!gm+", lat, ",", long ]
                    in
                        a
                            [ href mapUrl ]
                            [ Button.render
                                Mdl
                                [ 0 ]
                                model.mdl
                                [ Button.minifab ]
                                [ Icon.i "place"
                                , text (translate model.lang Map)
                                ]
                            ]

                Nothing ->
                    text ""

        Nothing ->
            text ""
