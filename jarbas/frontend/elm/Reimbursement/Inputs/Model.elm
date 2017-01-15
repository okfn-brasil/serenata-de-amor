module Reimbursement.Inputs.Model exposing (Model, Field, model)

import Dict
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material
import Reimbursement.Fields as Fields


type alias Field =
    { label : String
    , value : String
    }


type alias Model =
    { inputs : Dict.Dict String Field
    , lang : Language
    , mdl : Material.Model
    }


toFormField : ( String, String ) -> ( String, Field )
toFormField ( name, label ) =
    ( name, Field label "" )


model : Model
model =
    let
        pairs =
            List.map2 (,) Fields.names (Fields.labels English)

        inputs =
            List.filter Fields.isSearchable pairs
                |> List.map toFormField
                |> Dict.fromList
    in
        Model inputs English Material.model
