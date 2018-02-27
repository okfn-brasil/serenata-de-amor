module Reimbursement.Tweet.View exposing (view)

import Html exposing (a, text)
import Html.Attributes exposing (class, href, target)
import Internationalization exposing (translate)
import Internationalization.Types exposing (Language(..), TranslationId(..))
import Material.Button as Button
import Material.Icon as Icon
import Reimbursement.Tweet.Model exposing (Model)
import Reimbursement.Tweet.Update exposing (Msg(Mdl))


view : Model -> Html.Html Msg
view model =
    case model.url of
        Nothing ->
            text ""

        Just url ->
            a
                [ href url, target "_blank", class "tweet" ]
                [ Button.render
                    Mdl
                    [ 1 ]
                    model.mdl
                    [ Button.minifab ]
                    [ Icon.i "share"
                    , text (translate model.lang RosiesTweet)
                    ]
                ]
