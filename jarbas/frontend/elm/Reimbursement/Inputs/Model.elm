module Reimbursement.Inputs.Model exposing (Model, model)

import Material
import Reimbursement.Fields as Fields exposing (Field(..), Label(..), labels)


type alias Model =
    { inputs : List Field
    , mdl : Material.Model
    }


model : Model
model =
    let
        toFormField label =
            Field label ""

        inputs =
            List.filter (\(Label _ name) -> Fields.isSearchable name) labels
                |> List.map toFormField
    in
        { inputs = inputs
        , mdl = Material.model
        }
