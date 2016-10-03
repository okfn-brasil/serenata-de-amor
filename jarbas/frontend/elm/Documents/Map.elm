module Documents.Map exposing (view, viewFrom)

import Documents.Supplier as Supplier
import Material
import Material.Button as Button
import Material.Icon as Icon
import Html exposing (a, text)
import Html.Attributes exposing (href)
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
    , mdl : Material.Model
    }


modelFrom : Supplier.Model -> Model
modelFrom model =
    case model.supplier of
        Just supplier ->
            Model
                { latitude = supplier.latitude
                , longitude = supplier.longitude
                }
                Material.model

        Nothing ->
            Model
                { latitude = Nothing
                , longitude = Nothing
                }
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
                        url =
                            String.concat [ "https://ddg.gg/?q=!gm+", lat, ",", long ]
                    in
                        a
                            [ href url ]
                            [ Button.render
                                Mdl
                                [ 0 ]
                                model.mdl
                                [ Button.minifab ]
                                [ Icon.i "place"
                                , text " Supplier on Maps"
                                ]
                            ]

                Nothing ->
                    text ""

        Nothing ->
            text ""


viewFrom : Supplier.Model -> Html.Html Msg
viewFrom supplier =
    modelFrom supplier |> view
