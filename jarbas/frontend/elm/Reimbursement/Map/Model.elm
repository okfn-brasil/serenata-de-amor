module Reimbursement.Map.Model exposing (Model, modelFrom)

import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Reimbursement.Company.Model as Company


type alias GeoCoord =
    { latitude : Maybe String
    , longitude : Maybe String
    }


type alias Model =
    { geoCoord : GeoCoord
    , lang : Language
    , mdl : Material.Model
    }


modelFrom : Language -> Company.Model -> Model
modelFrom lang model =
    case model.company of
        Just company ->
            Model
                { latitude = company.latitude
                , longitude = company.longitude
                }
                lang
                Material.model

        Nothing ->
            Model
                { latitude = Nothing
                , longitude = Nothing
                }
                lang
                Material.model
