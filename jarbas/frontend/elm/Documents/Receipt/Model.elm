module Documents.Receipt.Model exposing (Model, model)

import Http
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material


type alias Model =
    { url : Maybe String
    , fetched : Bool
    , loading : Bool
    , error : Maybe Http.Error
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model Nothing False False Nothing English Material.model
