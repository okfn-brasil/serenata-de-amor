module Reimbursement.SameDay.Update exposing (..)

import Reimbursement.RelatedTable.Update exposing (Msg, loadUrl)
import String


type alias UniqueId =
    { applicantId : Int
    , year : Int
    , documentId : Int
    }


{-| Creates an URL from an UniqueId:

    >>> getUrl { year = 2016, applicantId = 13,  documentId = 42 }
    "/api/reimbursement/2016/13/42/same_day/?format=json"

-}
getUrl : UniqueId -> String
getUrl uniqueId =
    String.join
        "/"
        [ "/api"
        , "reimbursement"
        , uniqueId.year |> toString
        , uniqueId.applicantId |> toString
        , uniqueId.documentId |> toString
        , "same_day/?format=json"
        ]


load : UniqueId -> Cmd Msg
load uniqueId =
    uniqueId
        |> getUrl
        |> loadUrl
