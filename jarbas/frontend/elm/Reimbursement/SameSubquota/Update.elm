module Reimbursement.SameSubquota.Update exposing (..)

import Format.Url exposing (url)
import Reimbursement.RelatedTable.Update exposing (Msg, loadUrl)


type alias Filter =
    { applicantId : Int
    , year : Int
    , month : Int
    , subquotaId : Int
    }


{-| Creates an URL from a Filter:

    getUrl { year = 2016, applicantId = 13,  subquotaId = 42, month = 2 }
    --> "/api/chamber_of_deputies/reimbursement/?applicant_id=13&year=2016&month=2&subquota_id=42&format=json"

-}
getUrl : Filter -> String
getUrl filter =
    url "/api/chamber_of_deputies/reimbursement/"
        [ ( "applicant_id", toString filter.applicantId )
        , ( "year", toString filter.year )
        , ( "month", toString filter.month )
        , ( "subquota_id", toString filter.subquotaId )
        , ( "format", "json" )
        ]


load : Filter -> Cmd Msg
load filter =
    filter
        |> getUrl
        |> loadUrl
