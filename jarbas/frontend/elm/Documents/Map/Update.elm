module Documents.Map.Update exposing (Msg(..), update)

import Material
import Documents.Map.Model exposing (Model)


type Msg
    = Mdl (Material.Msg Msg)



-- FIXIT: the update function is not being used anywhere


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Mdl mdlMsg ->
            Material.update mdlMsg model
