module Reimbursement.Search.Model exposing (Model, model)

import Reimbursement.Fields as Fields exposing (Field(..), Label(..), labels)


type alias Model =
    List Field


model : Model
model =
    let
        toFormField label =
            Field label ""
    in
        List.filter (\(Label _ name) -> Fields.isSearchable name) labels
            |> List.map toFormField
