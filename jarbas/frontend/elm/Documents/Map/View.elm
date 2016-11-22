module Documents.Map.View exposing (view)

import Material.Button as Button
import Material.Icon as Icon
import Html exposing (a, text)
import Html.Attributes exposing (href)
import Internationalization exposing (Language(..), TranslationId(..), translate)
import String
import Documents.Map.Model exposing (Model)
import Documents.Map.Update exposing (Msg(Mdl))


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
