module Reimbursement.RelatedTable.Model exposing (ReimbursementSummary, Model, Results, model)

import Array exposing (Array)
import Internationalization.Types exposing (Language(..))
import Material


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
    { reimbursements : Array ReimbursementSummary
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
    Results Array.empty Nothing


model : Model
model =
    Model results Nothing English Material.model
