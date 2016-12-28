module Main exposing (..)

import Navigation
import Model exposing (Model, model)
import Update exposing (Flags, Msg(..), update, urlUpdate, updateFromFlags)
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
