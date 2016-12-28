module Documents.Company.Model exposing (Model, Company, Activity, model)

import Date
import Http
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material


type alias Activity =
    { code : String
    , description : String
    }


type alias Company =
    { main_activity : List Activity
    , secondary_activity : List Activity
    , cnpj : String
    , opening : Maybe Date.Date
    , legal_entity : Maybe String
    , trade_name : Maybe String
    , name : Maybe String
    , company_type : Maybe String
    , status : Maybe String
    , situation : Maybe String
    , situation_reason : Maybe String
    , situation_date : Maybe Date.Date
    , special_situation : Maybe String
    , special_situation_date : Maybe Date.Date
    , responsible_federative_entity : Maybe String
    , address : Maybe String
    , address_number : Maybe String
    , additional_address_details : Maybe String
    , neighborhood : Maybe String
    , zip_code : Maybe String
    , city : Maybe String
    , state : Maybe String
    , email : Maybe String
    , phone : Maybe String
    , latitude : Maybe String
    , longitude : Maybe String
    , last_updated : Maybe Date.Date
    }


type alias Model =
    { company : Maybe Company
    , loading : Bool
    , loaded : Bool
    , error : Maybe Http.Error
    , googleStreetViewApiKey : String
    , lang : Language
    , mdl : Material.Model
    }


model : Model
model =
    Model Nothing False False Nothing "" English Material.model
