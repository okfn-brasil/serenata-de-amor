module Reimbursement.Tweet.Update exposing (Msg(..), update)

import Material
import Reimbursement.Tweet.Model exposing (Model)


type Msg
    = Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Mdl mdlMsg ->
            Material.update mdlMsg model
