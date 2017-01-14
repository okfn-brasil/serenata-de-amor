module Reimbursement.RelatedTable.Model exposing (ReimbursementSummary, Model, Results, model)

import Material
import Internationalization exposing (Language(..))


type alias ReimbursementSummary =
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
    { reimbursements : List ReimbursementSummary
    , nextPageUrl : Maybe String
    }


type alias Model =
    { results : Results
    , parentId : Maybe Int
    , lang : Language
    , mdl : Material.Model
    }


results : Results
results =
    Results [] Nothing


model : Model
model =
    Model results Nothing English Material.model
