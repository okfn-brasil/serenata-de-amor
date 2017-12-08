module Reimbursement.Map.View exposing (view)

import Html exposing (a, text)
import Html.Attributes exposing (href, target)
import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..))
import Material.Button as Button
import Material.Icon as Icon
import Reimbursement.Map.Model exposing (Model)
import Reimbursement.Map.Update exposing (Msg(Mdl))
import String


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
                            [ href mapUrl, target "_blank" ]
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
