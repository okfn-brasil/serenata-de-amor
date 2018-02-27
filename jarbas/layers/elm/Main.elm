module Main exposing (..)

import Model exposing (Model, model)
import Navigation
import Update exposing (Flags, Msg(..), update, updateFromFlags, urlUpdate)
import View exposing (view)


init : Flags -> Navigation.Location -> ( Model, Cmd Msg )
init flags location =
    urlUpdate location (updateFromFlags flags model)


main : Program Flags Model Msg
main =
    Navigation.programWithFlags ChangeUrl
        { init = init
        , update = update
        , view = view
        , subscriptions = (\_ -> Sub.none)
        }
