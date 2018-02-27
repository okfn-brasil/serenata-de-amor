module Model exposing (Model, model)

import Internationalization.Types exposing (Language(..))
import Layout
import Material
import Reimbursement.Model as Reimbursement


type alias Model =
    { reimbursements : Reimbursement.Model
    , layout : Layout.Model
    , googleStreetViewApiKey : Maybe String
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    { reimbursements = Reimbursement.model
    , layout = Layout.model
    , googleStreetViewApiKey = Nothing
    , lang = English
    , mdl = Material.model
    }
