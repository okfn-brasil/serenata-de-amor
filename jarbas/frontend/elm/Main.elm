module Main exposing (..)

import Navigation
import Model exposing (Model, model)
import Update exposing (Flags, Msg(..), update, updateFromFlags)
import View exposing (view)
import Routes exposing (urlParser, urlUpdate)


init : Flags -> List ( String, String ) -> ( Model, Cmd Msg )
init flags query =
    urlUpdate query (updateFromFlags flags model)


main : Platform.Program Flags
main =
    Navigation.programWithFlags urlParser
        { init = init
        , update = update
        , urlUpdate = urlUpdate
        , view = view
        , subscriptions = (\_ -> Sub.none)
        }
