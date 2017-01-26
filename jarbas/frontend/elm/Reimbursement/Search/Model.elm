module Reimbursement.Search.Model exposing (Model, model)

import Reimbursement.Fields as Fields exposing (Field(..), Label(..), searchableLabels)


type alias Model =
    List Field


model : Model
model =
    let
        toFormField label =
            Field (Tuple.first label) ""
    in
        List.map toFormField searchableLabels
