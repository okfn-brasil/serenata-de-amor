module Model exposing (Model, model)

import Documents.Model
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Layout
import Material


type alias Model =
    { documents : Documents.Model.Model
    , layout : Layout.Model
    , googleStreetViewApiKey : Maybe String
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model Documents.Model.model Layout.model Nothing English Material.model
