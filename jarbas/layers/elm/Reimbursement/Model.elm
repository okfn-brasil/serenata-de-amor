module Reimbursement.Model exposing (..)

import Array exposing (Array)
import Date
import Http
import Internationalization.Types exposing (Language(..))
import Material
import Reimbursement.Company.Model as Company
import Reimbursement.Receipt.Model as Receipt
import Reimbursement.RelatedTable.Model as RelatedTable
import Reimbursement.Search.Model as Search


type alias Reimbursement =
    { year : Int
    , documentId : Int
    , applicantId : Int
    , totalReimbursementValue : Maybe Float
    , totalNetValue : Float
    , reimbursementNumbers : List Int
    , netValues : List Float
    , congresspersonId : Maybe Int
    , congresspersonName : Maybe String
    , congresspersonDocument : Maybe Int
    , state : Maybe String
    , party : Maybe String
    , termId : Maybe Int
    , term : Int
    , subquotaId : Int
    , subquotaDescription : String
    , subquotaGroupId : Maybe Int
    , subquotaGroupDescription : Maybe String
    , supplier : String
    , cnpjCpf : Maybe String
    , documentType : Int
    , documentNumber : Maybe String
    , documentValue : Float
    , issueDate : Date.Date
    , month : Int
    , remarkValue : Maybe Float
    , installment : Maybe Int
    , batchNumber : Maybe Int
    , reimbursementValues : Maybe (List Float)
    , passenger : Maybe String
    , legOfTheTrip : Maybe String
    , probability : Maybe Float
    , suspicions : Maybe (List ( String, Bool ))
    , tweet : Maybe String
    , receipt : Receipt.Model
    , supplierInfo : Company.Model
    , sameDay : RelatedTable.Model
    , sameSubquota : RelatedTable.Model
    , inLatestDataset : Bool
    }


type alias Results =
    { reimbursements : Array Reimbursement
    , total : Maybe Int
    , previous : Maybe String
    , next : Maybe String
    , loadingPage : Maybe Int
    , pageLoaded : Int
    , jumpTo : Maybe Int
    }


type alias Model =
    { results : Results
    , searchFields : Search.Model
    , showForm : Bool
    , loading : Bool
    , error : Maybe Http.Error
    , googleStreetViewApiKey : Maybe String
    , lang : Language
    , mdl : Material.Model
    }


results : Results
results =
    Results
        Array.empty
        Nothing
        Nothing
        Nothing
        Nothing
        1
        (Just 1)


model : Model
model =
    Model
        results
        Search.model
        True
        False
        Nothing
        Nothing
        English
        Material.model
