module Documents.SameDay.Model exposing (DocumentSummary, Model, Results, UniqueId, model)

import Material
import Internationalization exposing (Language(..))


type alias UniqueId =
    { applicantId : Int
    , year : Int
    , documentId : Int
    }


type alias DocumentSummary =
    { applicantId : Int
    , city : Maybe String
    , documentId : Int
    , subquotaDescription : String
    , subquotaId : Int
    , supplier : String
    , totalNetValue : Float
    , year : Int
    , over : Bool
    }


type alias Results =
    { documents : List DocumentSummary
    , nextPageUrl : Maybe String
    }


type alias Model =
    { results : Results
    , lang : Language
    , mdl : Material.Model
    }


results : Results
results =
    Results [] Nothing


model : Model
model =
    Model results English Material.model
