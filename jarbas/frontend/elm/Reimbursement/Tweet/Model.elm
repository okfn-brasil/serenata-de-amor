module Reimbursement.Tweet.Model exposing (Model, modelFrom)

import Internationalization.Types exposing (Language(..))
import Material


type alias Model =
    { url : Maybe String
    , lang : Language
    , mdl : Material.Model
    }


modelFrom : Language -> Maybe String -> Model
modelFrom lang url =
    Model url lang Material.model
