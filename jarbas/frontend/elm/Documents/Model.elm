module Documents.Model exposing (..)

import Documents.Inputs.Model as Inputs
import Documents.Receipt as Receipt
import Documents.Supplier as Supplier
import Http
import Internationalization exposing (Language(..), TranslationId(..), translate)
import Material


--
-- Model
--


type alias Document =
    { id : Int
    , document_id : Int
    , congressperson_name : String
    , congressperson_id : Int
    , congressperson_document : Int
    , term : Int
    , state : String
    , party : String
    , term_id : Int
    , subquota_number : Int
    , subquota_description : String
    , subquota_group_id : Int
    , subquota_group_description : String
    , supplier : String
    , cnpj_cpf : String
    , document_number : String
    , document_type : Int
    , issue_date : Maybe String
    , document_value : String
    , remark_value : String
    , net_value : String
    , month : Int
    , year : Int
    , installment : Int
    , passenger : String
    , leg_of_the_trip : String
    , batch_number : Int
    , reimbursement_number : Int
    , reimbursement_value : String
    , applicant_id : Int
    , receipt : Receipt.Model
    , supplier_info : Supplier.Model
    }


type alias Results =
    { documents : List Document
    , total : Maybe Int
    , previous : Maybe String
    , next : Maybe String
    , loadingPage : Maybe Int
    , pageLoaded : Int
    , jumpTo : String
    }


type alias Model =
    { results : Results
    , inputs : Inputs.Model
    , showForm : Bool
    , loading : Bool
    , error : Maybe Http.Error
    , googleStreetViewApiKey : String
    , lang : Language
    , mdl : Material.Model
    }


results : Results
results =
    Results [] Nothing Nothing Nothing Nothing 1 "1"


model : Model
model =
    Model results Inputs.model True False Nothing "" English Material.model
