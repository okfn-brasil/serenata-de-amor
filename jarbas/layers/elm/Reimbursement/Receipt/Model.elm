module Reimbursement.Receipt.Model exposing (Model, ReimbursementId, model)

import Http
import Internationalization.Types exposing (Language(..))
import Material


type alias ReimbursementId =
    { year : Int
    , applicantId : Int
    , documentId : Int
    }


type alias Model =
    { reimbursement : Maybe ReimbursementId
    , url : Maybe String
    , fetched : Bool
    , loading : Bool
    , error : Maybe Http.Error
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model Nothing Nothing False False Nothing English Material.model
