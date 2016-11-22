module Documents.Map.Model exposing (Model, modelFrom)

import Documents.Supplier as Supplier
import Material
import Internationalization exposing (Language(..), TranslationId(..), translate)


type alias GeoCoord =
    { latitude : Maybe String
    , longitude : Maybe String
    }


type alias Model =
    { geoCoord : GeoCoord
    , lang : Language
    , mdl : Material.Model
    }


modelFrom : Language -> Supplier.Model -> Model
modelFrom lang model =
    case model.supplier of
        Just supplier ->
            Model
                { latitude = supplier.latitude
                , longitude = supplier.longitude
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
