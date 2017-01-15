module Model exposing (Model, model)

import Reimbursement.Model as Reimbursement
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Layout
import Material


type alias Model =
    { reimbursements : Reimbursement.Model
    , layout : Layout.Model
    , googleStreetViewApiKey : Maybe String
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model
        Reimbursement.model
        Layout.model
        Nothing
        English
        Material.model
