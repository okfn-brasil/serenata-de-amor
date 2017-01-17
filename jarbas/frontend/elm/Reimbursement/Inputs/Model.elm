module Reimbursement.Inputs.Model exposing (Model, Field, model)

import Dict
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Reimbursement.Fields as Fields


type alias Field =
    { label : TranslationId
    , value : String
    }


type alias Model =
    { inputs : Dict.Dict String Field
    , mdl : Material.Model
    }


toFormField : ( String, TranslationId ) -> ( String, Field )
toFormField ( name, label ) =
    ( name, Field label "" )


model : Model
model =
    let
        pairs =
            List.map2 (,) Fields.names (Fields.labels)

        inputs =
            List.filter Fields.isSearchable pairs
                |> List.map toFormField
                |> Dict.fromList
    in
        { inputs = inputs
        , mdl = Material.model
        }
